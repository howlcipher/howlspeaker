"""Setup tooling must refuse expensive work without enforceable protection."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location(
    "qwen_check", Path(__file__).parents[1] / "scripts/qwen_check.py",
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_guard_checks_every_budget(monkeypatch, tmp_path):
    group = tmp_path / "group"
    group.mkdir()
    values = {
        'memory.high': '3221225472', 'memory.max': '5368709120',
        'memory.swap.max': '0', 'cpu.max': '150000 100000', 'pids.max': '192',
    }
    for key, value in values.items():
        (group / key).write_text(value)
    original = Path

    def fake_path(value):
        if value == '/proc/self/cgroup':
            return SimpleNamespace(read_text=lambda: '0::/group\n')
        if value == '/sys/fs/cgroup':
            return tmp_path
        return original(value)

    monkeypatch.setattr(check, 'Path', fake_path)
    assert check.verified_cgroup() == group
    for key, value in values.items():
        (group / key).write_text('max')
        with pytest.raises(ValueError, match='not enforced'):
            check.verified_cgroup()
        (group / key).write_text(value)


def test_missing_protection_prevents_download(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'qwen_check', 'download', '--model-dir', '/unused',
        '--manifest', '/unused.json',
    ])

    def rejected():
        raise ValueError('Required cgroup limits are not enforced')

    monkeypatch.setattr(check, 'verified_cgroup', rejected)
    monkeypatch.setattr(check, 'load_manifest', lambda *a: pytest.fail(
        'Manifest must not be touched before protection is verified',
    ))
    with pytest.raises(ValueError, match='not enforced'):
        check.main()
