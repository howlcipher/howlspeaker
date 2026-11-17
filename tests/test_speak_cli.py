import json

import pytest

import howlspeaker.cli as cli
from howlspeaker.profiles import ProfileStore
from howlspeaker.provider import GeneratedResult
from howlspeaker.voice import validate_voice
from test_voice import wav_bytes


@pytest.fixture
def setup(tmp_path, monkeypatch):
    voice = tmp_path / 'reference.wav'
    voice.write_bytes(wav_bytes())
    transcript = tmp_path / 'transcript.txt'
    transcript.write_text('Private reference words')
    calls = []

    class Adapter:
        execution_kind = 'local_inference'
        requires_transcript = True

        def __init__(self, **kwargs):
            calls.append(('init', kwargs))

        def synthesize(self, request):
            calls.append(('synthesize', request))
            return GeneratedResult(wav_bytes(), dict(
                exit_code=0, duration_seconds=0.1,
                peak_memory_bytes=1000000, swap_peak_bytes=0,
            ), 'controlled-test', 'a' * 40)

    monkeypatch.setattr('howlspeaker.qwen.QwenProvider', Adapter)
    prefix = ['speak', '--engine-python', '/approved/python',
              '--model-dir', '/approved/models',
              '--manifest', '/manifest.json',
              '--text', 'Private target script',
              '--out', str(tmp_path/'out.wav')]
    return tmp_path, voice, transcript, prefix, calls


def test_direct_sample_speak_export_private_output(setup, capsys):
    root, voice, transcript, prefix, calls = setup
    assert cli.main(prefix + ['--voice', str(voice), '--authorized',
                              '--provenance', 'Own private voice',
                              '--transcript-file', str(transcript)]) == 0
    assert [call[0] for call in calls] == ['init', 'synthesize']
    report = json.loads(capsys.readouterr().out)
    assert report['evidence_kind'] == 'generated_unreviewed'
    assert report['measurements']['peak_memory_bytes'] == 1000000
    assert b'synthetic' in (root/'out.wav').read_bytes()
    assert 'Private' not in json.dumps(report)


def test_profile_selection_hands_selected_snapshot_to_provider(setup, capsys):
    root, voice, _, prefix, calls = setup
    store = ProfileStore(root/'voices')
    store.add('speaker_a', 'take_01', validate_voice(
        voice, authorized=True, provenance='Own voice',
        transcript='First words',
    ))
    store.add('speaker_b', 'take_02', validate_voice(
        voice, authorized=True, provenance='Own voice',
        transcript='Second words',
    ))
    assert cli.main(prefix + ['--profile', 'speaker_b', '--take', 'take_02',
                              '--store', str(store.root), '--authorized']) == 0
    assert calls[-1][1].voice.transcript == 'Second words'
    assert 'Second words' not in capsys.readouterr().out


def test_missing_authority_never_constructs_provider(setup):
    _, voice, _, prefix, calls = setup
    assert cli.main(prefix + ['--voice', str(voice),
                              '--provenance', 'Own voice']) == 2
    assert not calls


@pytest.mark.parametrize('extra', [
    ['--profile', 'speaker', '--authorized'],
    ['--voice', '/absent', '--take', 'take_01', '--authorized',
     '--provenance', 'Own voice'],
    ['--profile', 'speaker', '--take', 'take_01', '--authorized',
     '--transcript', 'Cannot override stored consent'],
])
def test_ambiguous_selection_rejected_before_provider(setup, extra):
    _, _, _, prefix, calls = setup
    assert cli.main(prefix + extra) == 2
    assert not calls


def test_existing_output_refused_before_provider(setup):
    root, voice, transcript, prefix, calls = setup
    target = root/'out.wav'
    target.write_bytes(b'existing')
    assert cli.main(prefix + ['--voice', str(voice), '--authorized',
                              '--provenance', 'Own voice',
                              '--transcript-file', str(transcript)]) == 2
    assert target.read_bytes() == b'existing'
    assert not calls


def test_text_file_option_and_missing_transcript_rejected(setup):
    root, voice, transcript, prefix, calls = setup
    text_index = prefix.index('--text')
    prefix[text_index:text_index+2] = ['--text-file', str(root/'script.txt')]
    (root/'script.txt').write_text('Private file script')
    assert cli.main(prefix + ['--voice', str(voice), '--authorized',
                              '--provenance', 'Own voice',
                              '--transcript-file', str(transcript)]) == 0
    assert calls[-1][1].text == 'Private file script'
    (root/'out.wav').unlink()
    calls.clear()
    assert cli.main(prefix + ['--voice', str(voice), '--authorized',
                              '--provenance', 'Own voice']) == 2
    assert not calls


def test_failed_synthesis_prints_safe_metrics_without_publishing(
        setup, capsys, monkeypatch):
    from howlspeaker.provider import SynthesisFailure
    root, voice, transcript, prefix, _ = setup

    def fail(self, request):
        raise SynthesisFailure(dict(
            exit_code=124, duration_seconds=120,
            peak_memory_bytes=1000000, swap_peak_bytes=0,
        ))

    monkeypatch.setattr('howlspeaker.qwen.QwenProvider.synthesize', fail)
    assert cli.main(prefix + ['--voice', str(voice), '--authorized',
                              '--provenance', 'Own private voice',
                              '--transcript-file', str(transcript)]) == 2
    assert not (root/'out.wav').exists()
    captured = capsys.readouterr()
    assert '"exit_code": 124' in captured.err
    assert 'Private' not in captured.err
    assert captured.out == ''
