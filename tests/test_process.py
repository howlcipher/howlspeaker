import io
import json
import os
import subprocess

import pytest

import howlspeaker.process as module
from howlspeaker.process import SystemdMediaRunner


@pytest.fixture
def execution(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    record = {"stopped": [], "payload": b"\0" * 10,
              "report": dict(exit_code=0, duration_seconds=0.1,
                             peak_memory_bytes=1000000, swap_peak_bytes=0)}

    class Launcher:
        pid = 12345
        returncode = 0

        def __init__(self, command, **kwargs):
            record["command"] = command
            record["kwargs"] = kwargs
            kwargs["stdout"].write(record["payload"])
            if record["report"] is not None:
                kwargs["stderr"].write(
                    b"HOWLSPEAKER_REPORT "
                    + json.dumps(record["report"]).encode() + b"\n",
                )

        def wait(self, timeout):
            return self.returncode

        def poll(self):
            return self.returncode

    record["launcher"] = Launcher
    monkeypatch.setattr(subprocess, "Popen", Launcher)
    monkeypatch.setattr(module, "_stop_service", record["stopped"].append)
    return record


def convert(runner=None, **kwargs):
    return (runner or SystemdMediaRunner()).convert(
        io.BytesIO(b"fixture"), ["-version"],
        **(dict(max_output_bytes=100, timeout=2) | kwargs),
    )


def test_resource_properties_and_cleanup(execution):
    result = convert()
    command = execution["command"]
    for property_value in (
        "MemoryHigh=3221225472", "MemoryMax=5368709120", "MemorySwapMax=0",
        "CPUQuota=150%", "TasksMax=192", "KillMode=control-group",
        "NoNewPrivileges=yes", "RestrictAddressFamilies=AF_UNIX",
    ):
        assert property_value in command
    assert execution["kwargs"]["start_new_session"] is True
    assert "shell" not in execution["kwargs"]
    assert len(execution["stopped"]) == 1
    assert result.output == execution["payload"]
    assert result.peak_memory_bytes == 1000000


@pytest.mark.parametrize("values", [
    {"timeout": 0}, {"timeout": 31}, {"timeout": True},
    {"max_output_bytes": 0}, {"max_output_bytes": 10 * 1024**2 + 1},
])
def test_invalid_limits_do_not_launch(execution, values):
    with pytest.raises(ValueError):
        convert(**values)
    assert "command" not in execution


@pytest.mark.parametrize("report", [
    None, {}, {"exit_code": 0},
    dict(exit_code=0, duration_seconds=float("nan"),
         peak_memory_bytes=1000, swap_peak_bytes=0),
    dict(exit_code=0, duration_seconds=0.1,
         peak_memory_bytes=1000, swap_peak_bytes=1),
    dict(exit_code=0, duration_seconds=0.1,
         peak_memory_bytes=6 * 1024**3, swap_peak_bytes=0),
])
def test_unverified_execution_rejected(execution, report):
    execution["report"] = report
    with pytest.raises(ValueError):
        convert()
    assert len(execution["stopped"]) == 1


def test_output_overflow_rejected_and_cleaned(execution):
    execution["payload"] = b"x" * 101
    with pytest.raises(ValueError):
        convert()
    assert len(execution["stopped"]) == 1


def test_cancellation_cleans_service(execution, monkeypatch):
    def interrupt(self, timeout):
        raise KeyboardInterrupt()
    monkeypatch.setattr(execution["launcher"], "wait", interrupt)
    with pytest.raises(KeyboardInterrupt):
        convert()
    assert len(execution["stopped"]) == 1


def test_busy_worker_does_not_launch(execution, tmp_path):
    import fcntl
    lock_path = tmp_path / f"howlspeaker-media-{os.getuid()}.lock"
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="busy"):
            convert()
    assert "command" not in execution


def test_launcher_timeout_kills_owned_group(execution, monkeypatch):
    calls = []
    launcher = execution["launcher"]
    launcher.returncode = None

    def wait(self, timeout):
        if not calls:
            calls.append("timeout")
            raise subprocess.TimeoutExpired("private command", timeout)
        self.returncode = -9
        return -9

    monkeypatch.setattr(launcher, "wait", wait)
    killed = []
    monkeypatch.setattr(os, "killpg", lambda pid, sig: killed.append(pid))
    with pytest.raises(ValueError, match="timed out"):
        convert()
    assert len(execution["stopped"]) == 1
    assert killed == [12345]
