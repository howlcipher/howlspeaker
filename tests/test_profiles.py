import json
import subprocess
from pathlib import Path

import pytest

from howlspeaker.profiles import ProfileStore
from howlspeaker.voice import validate_voice
from test_voice import wav_bytes


@pytest.fixture
def voice(tmp_path):
    sample = tmp_path / 'input.wav'
    sample.write_bytes(wav_bytes())
    return validate_voice(sample, authorized=True,
                          provenance='My own recording',
                          transcript='Exact words spoken')


def test_swapping_is_explicit_and_profiles_survive_source_deletion(
        tmp_path, voice):
    store = ProfileStore(tmp_path / 'private')
    store.add('speaker_a', 'natural_01', voice, delivery='natural')
    store.add('speaker_a', 'narration_01', voice, delivery='narration')
    store.add('speaker_b', 'natural_01', voice, delivery='relaxed')
    (tmp_path / 'input.wav').unlink()
    assert len(store.list()) == 3
    loaded = store.load('speaker_b', 'natural_01')
    assert loaded.audio_bytes == voice.audio_bytes
    assert loaded.provenance == voice.provenance
    assert loaded.transcript == voice.transcript
    metadata = store.describe('speaker_a', 'narration_01')
    assert metadata['delivery'] == 'narration'
    assert metadata['duration_seconds'] == 1
    assert metadata['transcript_sha256']
    assert 'Exact words' not in json.dumps(metadata)
    assert 'My own' not in json.dumps(metadata)
    assert store.root.stat().st_mode & 0o777 == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600
               for p in store.root.iterdir())
    with pytest.raises(ValueError):
        store.add('speaker_a', 'natural_01', voice)
    store.delete('speaker_a', 'natural_01')
    assert len(store.list()) == 2
    assert (store.load('speaker_b', 'natural_01').audio_bytes
            == voice.audio_bytes)
    with pytest.raises(ValueError):
        store.load('speaker_a', 'natural_01')


@pytest.mark.parametrize('name', ['../escape', '/tmp/x', 'a--b', '', 'x\ny'])
def test_ids_reject_traversal(tmp_path, voice, name):
    store = ProfileStore(tmp_path / 'private')
    with pytest.raises(ValueError):
        store.add(name, 'take_01', voice)
    assert not store.root.exists()


def test_symlink_store_and_profile_cannot_be_followed(tmp_path, voice):
    outside = tmp_path / 'outside'
    outside.mkdir()
    root = tmp_path / 'private'
    root.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        ProfileStore(root).add('speaker', 'take_01', voice)
    assert not list(outside.iterdir())
    root.unlink()
    root.mkdir(mode=0o700)
    target = root / 'speaker--take_01.json'
    secret = outside / 'secret.json'
    secret.write_text('private')
    target.symlink_to(secret)
    with pytest.raises(ValueError):
        ProfileStore(root).load('speaker', 'take_01')
    assert secret.read_text() == 'private'


def test_tampered_audio_and_consent_fail_closed(tmp_path, voice):
    store = ProfileStore(tmp_path / 'private')
    store.add('speaker', 'take_01', voice)
    path = store.root / 'speaker--take_01.json'
    original = json.loads(path.read_text())
    for field, value in [('audio_base64', 'AAAA'), ('authorized', False),
                         ('transcript', 'changed'), ('profile_id', 'other')]:
        path.write_text(json.dumps(original | {field: value}))
        with pytest.raises(ValueError):
            store.load('speaker', 'take_01')


def test_profile_store_refuses_shared_permissions(tmp_path, voice):
    root = tmp_path / 'shared'
    root.mkdir(mode=0o755)
    with pytest.raises(ValueError):
        ProfileStore(root).add('speaker', 'take_01', voice)
    assert not list(root.iterdir())


def test_git_ignores_private_profiles_and_recordings():
    repo = Path(__file__).parents[1]
    result = subprocess.run([
        'git', 'check-ignore', 'profiles/speaker/consent.json',
        'voices/speaker.json', '.howlspeaker/profile.json',
        'recordings/take.wav',
    ], cwd=repo, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0
    assert len(result.stdout.splitlines()) == 4


def test_cli_add_list_show_delete(tmp_path, voice, capsys):
    from howlspeaker.cli import main
    transcript = tmp_path / 'transcript.txt'
    transcript.write_text(voice.transcript)
    prefix = ['profile', '--store', str(tmp_path / 'private')]
    assert main(prefix + [
        'add', '--id', 'speaker', '--take', 'natural_01',
        '--voice', str(tmp_path / 'input.wav'), '--authorized',
        '--provenance', voice.provenance,
        '--transcript-file', str(transcript), '--delivery', 'natural',
    ]) == 0
    assert main(prefix + ['list']) == 0
    assert main(prefix + ['show', '--id', 'speaker',
                          '--take', 'natural_01']) == 0
    output = capsys.readouterr().out
    assert voice.transcript not in output
    assert voice.provenance not in output
    assert main(prefix + ['delete', '--id', 'speaker',
                          '--take', 'natural_01']) == 0
    assert main(prefix + ['show', '--id', 'speaker',
                          '--take', 'natural_01']) == 2


def test_missing_consent_never_creates_store(tmp_path, capsys):
    from howlspeaker.cli import main
    root = tmp_path / 'private'
    assert main(['profile', '--store', str(root), 'add', '--id', 'speaker',
                 '--take', 'take_01', '--voice', '/absent',
                 '--provenance', 'private basis']) == 2
    assert not root.exists()
    assert 'private basis' not in capsys.readouterr().err


def test_distinct_speakers_and_takes_return_distinct_snapshots(
        tmp_path, voice):
    from dataclasses import replace
    store = ProfileStore(tmp_path / 'private')
    other = replace(voice, audio_bytes=wav_bytes(frames=4000),
                    transcript='A different recording',
                    provenance='Another authorized fixture')
    store.add('first', 'take_01', voice)
    store.add('first', 'take_02', other)
    store.add('second', 'take_01', other)
    assert (store.load('first', 'take_01').audio_bytes
            == voice.audio_bytes)
    assert store.load('first', 'take_02').audio_bytes == other.audio_bytes
    assert store.load('second', 'take_01').transcript == other.transcript
    assert store.describe('first', 'take_02')['duration_seconds'] == 0.5


def test_atomic_publication_failure_leaves_no_partial(
        tmp_path, voice, monkeypatch):
    store = ProfileStore(tmp_path / 'private')

    def fail(*args, **kwargs):
        raise OSError('private details')

    monkeypatch.setattr('howlspeaker.profiles.os.link', fail)
    with pytest.raises(ValueError, match='Cannot save'):
        store.add('speaker', 'take_01', voice)
    assert not list(store.root.iterdir())


def test_default_store_outside_repo(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path))
    assert ProfileStore().root == tmp_path / 'howlspeaker/voices'
    monkeypatch.setenv('XDG_DATA_HOME', 'relative')
    with pytest.raises(ValueError, match='absolute'):
        ProfileStore()


def test_private_file_permissions_and_current_limits_enforced(tmp_path, voice):
    from howlspeaker.config import Configuration
    store = ProfileStore(tmp_path / 'private')
    store.add('speaker', 'take_01', voice)
    path = store.root / 'speaker--take_01.json'
    path.chmod(0o644)
    with pytest.raises(ValueError):
        store.load('speaker', 'take_01')
    path.chmod(0o600)
    limited = ProfileStore(store.root, Configuration(max_voice_bytes=100))
    with pytest.raises(ValueError):
        limited.load('speaker', 'take_01')


def test_profile_snapshot_has_bounded_read(tmp_path, voice):
    store = ProfileStore(tmp_path / 'private')
    store.add('speaker', 'take_01', voice)
    path = store.root / 'speaker--take_01.json'
    with path.open('wb') as stream:
        stream.truncate(20 * 1024**2)
    with pytest.raises(ValueError):
        store.load('speaker', 'take_01')


@pytest.mark.parametrize('payload', [b'null', b'[]', b'{',
                                     b'{"schema":true}', b'\xff'])
def test_malformed_snapshot_private_error(tmp_path, voice, payload):
    store = ProfileStore(tmp_path / 'private')
    store.add('speaker', 'take_01', voice)
    path = store.root / 'speaker--take_01.json'
    path.write_bytes(payload)
    with pytest.raises(ValueError, match='Cannot load a valid private'):
        store.load('speaker', 'take_01')
