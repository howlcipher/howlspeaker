"""Strict M0 configuration; resource values are budgets, not enforcement."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Configuration:
    provider: str = "disabled"
    remote_enabled: bool = False
    workers: int = 1
    retries: int = 0
    memory_high_bytes: int = 3 * 1024**3
    memory_max_bytes: int = 5 * 1024**3
    memory_swap_max_bytes: int = 0
    cpu_quota_percent: int = 150
    tasks_max: int = 192
    timeout_seconds: int = 120
    max_script_chars: int = 500
    max_voice_bytes: int = 10 * 1024**2
    max_voice_seconds: int = 30
    max_output_bytes: int = 10 * 1024**2
    max_output_seconds: int = 30

    def __post_init__(self) -> None:
        defaults = {
            "workers": (1, 1), "retries": (0, 0),
            "memory_high_bytes": (1, 3 * 1024**3),
            "memory_max_bytes": (1, 5 * 1024**3),
            "memory_swap_max_bytes": (0, 0),
            "cpu_quota_percent": (1, 150), "tasks_max": (1, 192),
            "timeout_seconds": (1, 120), "max_script_chars": (1, 500),
            "max_voice_bytes": (1, 10 * 1024**2),
            "max_voice_seconds": (1, 30),
            "max_output_bytes": (1, 10 * 1024**2),
            "max_output_seconds": (1, 30),
        }
        for name, (low, high) in defaults.items():
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"Invalid safety setting: {name}")
        if self.memory_high_bytes > self.memory_max_bytes:
            raise ValueError("Memory high exceeds memory maximum")
        if self.provider != "disabled" or self.remote_enabled is not False:
            raise ValueError("Inference is unavailable in M0")

    def to_dict(self) -> dict:
        return asdict(self)


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate configuration key")
        result[key] = value
    return result


def load_configuration(path: Path | None = None) -> Configuration:
    if path is None:
        return Configuration()
    try:
        with path.open("rb") as source:
            data = source.read(65537)
        if len(data) > 65536:
            raise ValueError("Configuration too large")
        values = json.loads(data, object_pairs_hook=_unique_object)
        if not isinstance(values, dict):
            raise ValueError("Expected object")
        return Configuration(**values)
    except (OSError, ValueError, TypeError, UnicodeError):
        raise ValueError("Cannot load configuration; check file and schema") \
            from None
