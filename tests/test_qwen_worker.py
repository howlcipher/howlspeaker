"""No ML dependencies; authority and wire validation precede engine imports."""

import base64
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import howlspeaker.qwen_worker as worker
from howlspeaker.config import Configuration
from test_voice import wav_bytes


def payload():
    root = Path(__file__).parents[1]
    return dict(protocol=1, text='Private target text', authorized=True,
                provenance='Own fixture', transcript='Actual reference words',
                audio_base64=base64.b64encode(wav_bytes()).decode(),
                model_dir='/approved/models', config=Configuration().to_dict(),
                manifest=json.loads((root/'engines/qwen/model_manifest.json')
                                    .read_text()))


def test_guard_before_model_verification(monkeypatch):
    calls = []

    def protect(config):
        calls.append('protected')

    def verify(manifest, root, **kwargs):
        calls.append('verified')
        assert root == Path('/approved/models')

    monkeypatch.setattr(worker, 'require_protection', protect)
    monkeypatch.setattr(worker, 'verify_model', verify)
    text, voice, _, _ = worker.decode_request(io.BytesIO(
        json.dumps(payload()).encode(),
    ))
    assert calls == ['protected', 'verified']
    assert text == 'Private target text'
    assert voice.audio_bytes == wav_bytes()
    assert voice.transcript == 'Actual reference words'


def test_absent_guard_never_verifies_or_imports_engine(monkeypatch):
    def deny(config):
        raise ValueError('Required worker protection is absent')

    monkeypatch.setattr(worker, 'require_protection', deny)
    monkeypatch.setattr(worker, 'verify_model', lambda *a, **k: pytest.fail(
        'Model accessed before guard',
    ))
    with pytest.raises(ValueError, match='protection'):
        worker.decode_request(io.BytesIO(json.dumps(payload()).encode()))


@pytest.mark.parametrize('change', [
    {'protocol': True}, {'protocol': 2}, {'authorized': False},
    {'transcript': None}, {'text': 'x' * 501}, {'audio_base64': '!!!'},
    {'model_dir': 'relative'}, {'manifest': {}},
    {'config': {'workers': 2}},
])
def test_invalid_request_cannot_touch_model(monkeypatch, change):
    monkeypatch.setattr(worker, 'require_protection', lambda cfg: None)
    monkeypatch.setattr(worker, 'verify_model', lambda *a, **k: pytest.fail(
        'Invalid request touched model',
    ))
    with pytest.raises((ValueError, TypeError)):
        worker.decode_request(io.BytesIO(
            json.dumps(payload() | change).encode(),
        ))


def test_request_read_is_bounded(monkeypatch):
    monkeypatch.setattr(worker, 'MAX_REQUEST_BYTES', 20)
    with pytest.raises(ValueError, match='too large'):
        worker.decode_request(io.BytesIO(b'x' * 21))


def test_worker_rechecks_cgroup_fsize_and_network(monkeypatch, tmp_path):
    group = tmp_path/'group'
    group.mkdir()
    values = {
        'memory.high': '3221225472', 'memory.max': '5368709120',
        'memory.swap.max': '0', 'cpu.max': '150000 100000', 'pids.max': '192',
    }
    for key, value in values.items():
        (group/key).write_text(value)

    def fake_path(value):
        if value == '/proc/self/cgroup':
            return SimpleNamespace(read_text=lambda: '0::/group\n')
        if value == '/proc/meminfo':
            return SimpleNamespace(
                read_text=lambda: 'MemAvailable: 8000000 kB',
            )
        return tmp_path if value == '/sys/fs/cgroup' else Path(value)

    def denied_socket(family):
        raise OSError('denied')

    monkeypatch.setattr(worker, 'Path', fake_path)
    limit = Configuration().max_output_bytes
    monkeypatch.setattr(worker.resource, 'getrlimit',
                        lambda *a: (limit, limit))
    monkeypatch.setattr(worker.socket, 'socket', denied_socket)
    worker.require_protection(Configuration())
    for key, value in values.items():
        (group/key).write_text('max')
        with pytest.raises(ValueError):
            worker.require_protection(Configuration())
        (group/key).write_text(value)
    monkeypatch.setattr(worker.socket, 'socket',
                        lambda family: SimpleNamespace(close=lambda: None))
    with pytest.raises(ValueError, match='network'):
        worker.require_protection(Configuration())
    monkeypatch.setattr(worker.resource, 'getrlimit', lambda *a: (-1, -1))
    with pytest.raises(ValueError, match='file-size'):
        worker.require_protection(Configuration())


def test_low_host_memory_refuses_expensive_work(monkeypatch):
    original = worker.Path

    class FakeGroup:
        def __truediv__(self, key):
            if isinstance(key, Path):
                return self
            values = dict(zip(
                ('memory.high', 'memory.max', 'memory.swap.max', 'cpu.max',
                 'pids.max'),
                ('3221225472', '5368709120', '0', '150000 100000', '192'),
            ))
            return SimpleNamespace(read_text=lambda: values[key])

    def fake_path(value):
        if value == '/proc/self/cgroup':
            return SimpleNamespace(read_text=lambda: '0::/group\n')
        if value == '/sys/fs/cgroup':
            return FakeGroup()
        if value == '/proc/meminfo':
            return SimpleNamespace(read_text=lambda: 'MemAvailable: 1024 kB')
        return original(value)

    monkeypatch.setattr(worker, 'Path', fake_path)
    with pytest.raises(ValueError,
                       match='Host memory is below approved budget'):
        worker.require_protection(Configuration())
