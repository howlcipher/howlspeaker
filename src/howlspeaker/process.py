"""Serial, fail-closed systemd execution for bounded local media decoding."""

import fcntl
import json
import math
import os
import signal
import stat
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from howlspeaker.config import Configuration


# Runs in the host service without an application install or shared paths.
GUARD = r'''
import json, pathlib, resource, socket, subprocess, sys, time
budget = json.loads(sys.argv[1])
cgroup = pathlib.Path('/sys/fs/cgroup') / pathlib.Path(
    pathlib.Path('/proc/self/cgroup').read_text().split('0::', 1)[1].strip()
).relative_to('/')
expected = {
    'memory.high': str(budget['memory_high_bytes']),
    'memory.max': str(budget['memory_max_bytes']),
    'memory.swap.max': '0',
    'cpu.max': str(budget['cpu_quota_percent'] * 1000) + ' 100000',
    'pids.max': str(budget['tasks_max']),
}
if any((cgroup / key).read_text().strip() != value
       for key, value in expected.items()):
    sys.exit(125)
if resource.getrlimit(resource.RLIMIT_FSIZE) != (
        budget['file_size_limit'], budget['file_size_limit']):
    sys.exit(125)
for family in (socket.AF_INET, socket.AF_INET6):
    try:
        connection = socket.socket(family)
    except OSError:
        continue
    connection.close()
    sys.exit(125)
started = time.monotonic()
try:
    child = subprocess.run(sys.argv[2:], stdin=sys.stdin.buffer,
                           stdout=sys.stdout.buffer, stderr=subprocess.DEVNULL,
                           timeout=budget['timeout_seconds'], check=False)
    code = child.returncode
except subprocess.TimeoutExpired:
    code = 124
except OSError:
    code = 127
report = {
    'exit_code': code,
    'duration_seconds': time.monotonic() - started,
    'peak_memory_bytes': int((cgroup / 'memory.peak').read_text()),
    'swap_peak_bytes': int((cgroup / 'memory.swap.peak').read_text()),
}
print('HOWLSPEAKER_REPORT ' + json.dumps(report), file=sys.stderr, flush=True)
sys.exit(0 if code == 0 else 1)
'''


@dataclass(frozen=True)
class MediaRunResult:
    output: bytes = field(repr=False)
    exit_code: int
    duration_seconds: float
    peak_memory_bytes: int
    swap_peak_bytes: int

    def measurements(self) -> dict:
        return {
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "peak_memory_bytes": self.peak_memory_bytes,
            "swap_peak_bytes": self.swap_peak_bytes,
        }


def _control(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["systemctl", "--user", *arguments], stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=5, check=False,
    )


def _stop_service(unit: str) -> None:
    _control("stop", unit)
    active = _control("is-active", "--quiet", unit)
    if active.returncode == 0:
        _control("kill", "--signal=KILL", "--kill-whom=all", unit)
        _control("stop", unit)
        if _control("is-active", "--quiet", unit).returncode == 0:
            raise ValueError("Cannot confirm media worker cleanup")
    elif active.returncode not in (3, 4):
        raise ValueError("Cannot confirm media worker cleanup")
    _control("reset-failed", unit)


class SystemdMediaRunner:
    def __init__(self, config: Configuration | None = None, *,
                 ffmpeg: str = "ffmpeg") -> None:
        self._config = config if config is not None else Configuration()
        if (not isinstance(ffmpeg, str) or not ffmpeg
                or ffmpeg.startswith("-") or "\0" in ffmpeg
                or "\n" in ffmpeg):
            raise ValueError("Invalid FFmpeg executable setting")
        self._ffmpeg = ffmpeg

    def convert(
        self, source: BinaryIO, arguments: list[str], *,
        max_output_bytes: int, timeout: int,
    ) -> MediaRunResult:
        if (type(timeout) is not int or not 1 <= timeout <= 30
                or type(max_output_bytes) is not int
                or not 1 <= max_output_bytes <= self._config.max_voice_bytes):
            raise ValueError("Invalid media execution limits")
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())
        runtime = Path(runtime_dir)
        lock_path = runtime / f"howlspeaker-media-{os.getuid()}.lock"
        try:
            lock_fd = os.open(
                lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600,
            )
            with os.fdopen(lock_fd, "rb") as lock:
                info = os.fstat(lock.fileno())
                if (not stat.S_ISREG(info.st_mode)
                        or info.st_uid != os.getuid()
                        or info.st_nlink != 1):
                    raise ValueError("Unsafe media worker lock")
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise ValueError("Media worker is already busy") from None
                return self._execute(
                    source, arguments, max_output_bytes, timeout,
                )
        except (OSError, subprocess.SubprocessError):
            raise ValueError("Media service unavailable; check user systemd") \
                from None

    def _execute(self, source: BinaryIO, arguments: list[str],
                 output_limit: int, timeout: int) -> MediaRunResult:
        config = self._config
        budget = config.to_dict() | {
            "timeout_seconds": timeout,
            "file_size_limit": max(output_limit, 16384),
        }
        unit = "howlspeaker-media-" + uuid.uuid4().hex + ".service"
        properties = {
            "MemoryHigh": config.memory_high_bytes,
            "MemoryMax": config.memory_max_bytes,
            "MemorySwapMax": 0,
            "CPUQuota": str(config.cpu_quota_percent) + "%",
            "CPUQuotaPeriodSec": "100ms",
            "TasksMax": config.tasks_max,
            "RuntimeMaxSec": timeout + 2,
            "TimeoutStopSec": 2,
            "KillMode": "control-group",
            "SendSIGKILL": "yes",
            "NoNewPrivileges": "yes",
            "RestrictAddressFamilies": "AF_UNIX",
            "LimitFSIZE": max(output_limit, 16384),
        }
        command = ["systemd-run", "--user", "--quiet", "--wait", "--pipe",
                   "--unit=" + unit, "--expand-environment=no"]
        for name, value in properties.items():
            command.extend(["--property", f"{name}={value}"])
        thread_keys = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                       "MKL_NUM_THREADS")
        for key in thread_keys:
            command.append("--setenv=" + key + "=1")
        command.extend(["python3", "-c", GUARD, json.dumps(budget),
                        self._ffmpeg, *arguments])
        with (tempfile.TemporaryFile() as output,
              tempfile.TemporaryFile() as err):
            process = subprocess.Popen(
                command, stdin=source, stdout=output, stderr=err,
                start_new_session=True,
            )
            try:
                try:
                    process.wait(timeout=timeout + 7)
                except subprocess.TimeoutExpired:
                    raise ValueError("Media extraction timed out") from None
            finally:
                try:
                    _stop_service(unit)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            if output.tell() > output_limit or err.tell() > 16384:
                raise ValueError("Media worker exceeded output limit")
            output.seek(0)
            err.seek(0)
            payload = output.read(output_limit + 1)
            reports = [line.removeprefix(b"HOWLSPEAKER_REPORT ")
                       for line in err.read(16385).splitlines()
                       if line.startswith(b"HOWLSPEAKER_REPORT ")]
            if len(reports) != 1:
                raise ValueError("Media protection or FFmpeg is unavailable")
            try:
                report = json.loads(reports[0])
                result = MediaRunResult(payload, **report)
                if (type(result.peak_memory_bytes) is not int
                        or not 0 < result.peak_memory_bytes
                        <= config.memory_max_bytes
                        or type(result.swap_peak_bytes) is not int
                        or result.swap_peak_bytes != 0
                        or type(result.exit_code) is not int
                        or not -255 <= result.exit_code <= 255
                        or type(result.duration_seconds) not in (int, float)
                        or not math.isfinite(result.duration_seconds)
                        or not 0 <= result.duration_seconds <= timeout + 2):
                    raise ValueError("Invalid media measurements")
            except (ValueError, TypeError):
                raise ValueError("Invalid media worker report") from None
            if process.returncode != 0 and result.exit_code == 0:
                raise ValueError("Media worker failed after extraction")
            return result
