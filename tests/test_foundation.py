import json
import logging
import subprocess
import sys

import pytest

from howlspeaker.config import Configuration, load_configuration
from howlspeaker.diagnostics import configure_logging


def test_safe_defaults():
    config = Configuration()
    assert config.workers == 1
    assert config.provider == "disabled"
    assert config.memory_max_bytes == 5 * 1024**3
    assert config.memory_swap_max_bytes == 0


@pytest.mark.parametrize("values", [
    {"workers": 2}, {"workers": True}, {"provider": "qwen"},
    {"remote_enabled": True}, {"memory_max_bytes": 6 * 1024**3},
    {"memory_high_bytes": 6 * 1024**3}, {"memory_swap_max_bytes": 1},
    {"cpu_quota_percent": 151}, {"tasks_max": 193},
    {"timeout_seconds": 0}, {"timeout_seconds": float("nan")},
    {"max_script_chars": 0}, {"max_script_chars": 501},
    {"retries": 1}, {"max_voice_bytes": -1},
    {"max_voice_seconds": 31}, {"timeout_seconds": "10"},
])
def test_reject_unsafe_configuration(values):
    with pytest.raises(ValueError):
        Configuration(**values)


def test_load_valid_configuration(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"timeout_seconds": 30}', encoding="utf-8")
    assert load_configuration(path).timeout_seconds == 30


@pytest.mark.parametrize("content", [
    "[]", "null", '{"secret": "private"}', "{", '{"workers": NaN}',
    '{"workers": 1, "workers": 1}',
])
def test_bad_files_have_private_errors(tmp_path, content):
    path = tmp_path / "private.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError) as error:
        load_configuration(path)
    assert "private" not in str(error.value)


def test_logging_uses_allowlisted_fields():
    import io
    stream = io.StringIO()
    logger = logging.getLogger("test.howlspeaker")
    configure_logging(logger, stream)
    logger.info("private script", extra={"event": "config_validated"})
    record = json.loads(stream.getvalue())
    assert record["event"] == "config_validated"
    assert "private" not in stream.getvalue()
    assert record["level"] == "INFO"


def test_installed_cli_contract():
    result = subprocess.run(
        [sys.executable, "-m", "howlspeaker", "config"],
        capture_output=True, text=True, timeout=10,
        env=__import__("os").environ | {"PYTHONPATH": "src"},
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["provider"] == "disabled"


def test_cli_missing_config_is_actionable(tmp_path, capsys):
    from howlspeaker.cli import main
    assert main(["config", "--config", str(tmp_path / "missing")]) == 2
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("content", [b" " * 65537, b"\xff"])
def test_oversized_or_invalid_encoding_rejected(tmp_path, content):
    path = tmp_path / "config.json"
    path.write_bytes(content)
    with pytest.raises(ValueError):
        load_configuration(path)


def test_high_cannot_exceed_maximum():
    with pytest.raises(ValueError):
        Configuration(memory_max_bytes=1024)


def test_arbitrary_event_is_not_logged():
    import io
    stream = io.StringIO()
    logger = logging.getLogger("test.private")
    configure_logging(logger, stream)
    logger.error("secret", extra={"event": "secret"})
    assert json.loads(stream.getvalue())["event"] == "diagnostic"
    assert "secret" not in stream.getvalue()
