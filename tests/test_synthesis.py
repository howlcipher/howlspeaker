"""Controlled provider/CLI integration, never real synthesis acceptance."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from howlspeaker.config import Configuration
from howlspeaker.export import ExportService
from howlspeaker.narration import NarrationService
from howlspeaker.provider import SynthesisFailure
from howlspeaker.qwen import QwenProvider
from howlspeaker.process import MediaRunResult
from howlspeaker.voice import validate_voice
from test_voice import wav_bytes


@pytest.fixture
def reference(tmp_path):
    path = tmp_path / 'reference.wav'
    path.write_bytes(wav_bytes())
    return validate_voice(path, authorized=True, provenance='Own fixture',
                          transcript='Exact fixture transcript')


class ControlledRunner:
    def __init__(self):
        self.calls = []
        self.result = MediaRunResult(wav_bytes(), 0, 0.1, 1000000, 0)

    def run(self, source, command, **limits):
        self.calls.append((json.load(source), command, limits))
        return self.result


def provider(runner, config=None):
    manifest = Path(__file__).parents[1] / 'engines/qwen/model_manifest.json'
    return QwenProvider(engine_python=Path('/approved/env/bin/python'),
                        model_dir=Path('/approved/models'), manifest=manifest,
                        runner=runner, config=config)


def test_actual_snapshot_and_transcript_handoff_and_export(
        tmp_path, reference):
    import base64
    runner = ControlledRunner()
    result = NarrationService(provider(runner)).generate(
        text='Hello test.', voice=reference,
    )
    assert result.evidence_kind == 'generated_unreviewed'
    payload, command, limits = runner.calls[0]
    assert payload['text'] == 'Hello test.'
    assert payload['transcript'] == reference.transcript
    assert base64.b64decode(payload['audio_base64']) == reference.audio_bytes
    assert reference.transcript not in ' '.join(command)
    assert 'Hello test.' not in ' '.join(command)
    assert '-I' in command
    assert limits['timeout'] == 120
    assert len(runner.calls) == 1
    metadata = ExportService().export_generated(result, tmp_path, 'speech.wav')
    assert metadata['evidence_kind'] == 'generated_unreviewed'
    data = (tmp_path / 'speech.wav').read_bytes()
    assert b'synthetic' in data
    assert b'not real inference' not in data
    assert reference.transcript.encode() not in data
    with pytest.raises(ValueError):
        ExportService().export_generated(result, tmp_path, 'speech.wav')


@pytest.mark.parametrize('change', [
    {'authorized': False}, {'transcript': None}, {'audio_bytes': b'invalid'},
])
def test_invalid_reference_never_launches(reference, change):
    runner = ControlledRunner()
    with pytest.raises(ValueError):
        NarrationService(provider(runner)).generate(
            text='Hello', voice=replace(reference, **change),
        )
    assert not runner.calls


@pytest.mark.parametrize('text', ['', 'x' * 501, '\0private', 'bad\ud800'])
def test_invalid_script_never_launches(reference, text):
    runner = ControlledRunner()
    with pytest.raises(ValueError):
        NarrationService(provider(runner)).generate(text=text, voice=reference)
    assert not runner.calls


def test_failure_has_measurements_no_partial_export(reference):
    runner = ControlledRunner()
    runner.result = MediaRunResult(b'partial', 124, 120, 1000000, 0)
    with pytest.raises(SynthesisFailure) as caught:
        NarrationService(provider(runner)).generate(
            text='Hello', voice=reference,
        )
    assert caught.value.measurements['exit_code'] == 124
    assert len(runner.calls) == 1


@pytest.mark.parametrize('result', [
    MediaRunResult(b'bad WAV', 0, 0.1, 1000000, 0),
    MediaRunResult(wav_bytes(), 0, 0.1, 1000000, 1),
    MediaRunResult(wav_bytes(), 0, float('nan'), 1000000, 0),
])
def test_invalid_worker_output_rejected(reference, result):
    runner = ControlledRunner()
    runner.result = result
    with pytest.raises(ValueError):
        NarrationService(provider(runner)).generate(
            text='Hello', voice=reference,
        )


def test_provider_exceptions_private_and_no_retry(reference):
    runner = ControlledRunner()

    def fail(*args, **kwargs):
        runner.calls.append('failed')
        raise RuntimeError('private script and reference')

    runner.run = fail
    with pytest.raises(ValueError) as caught:
        NarrationService(provider(runner)).generate(
            text='Hello', voice=reference,
        )
    assert 'private' not in str(caught.value)
    assert len(runner.calls) == 1


def test_simulation_and_real_paths_cannot_be_interchanged(reference):
    runner = ControlledRunner()
    service = NarrationService(provider(runner))
    with pytest.raises(ValueError):
        service.simulate(text='Hello', voice_path=Path('/absent'),
                         authorized=True, provenance='fixture')
    assert not runner.calls


def test_lowered_timeout_and_output_limits(reference):
    runner = ControlledRunner()
    config = Configuration(timeout_seconds=2, max_output_seconds=1)
    NarrationService(provider(runner, config), config).generate(
        text='Hello', voice=reference,
    )
    payload, _, limits = runner.calls[0]
    assert payload['config']['max_output_seconds'] == 1
    assert limits['timeout'] == 2


def test_failure_report_cannot_expose_provider_payload(reference):
    runner = ControlledRunner()

    def fail(*args, **kwargs):
        raise SynthesisFailure({'private_transcript': 'secret'})

    runner.run = fail
    with pytest.raises(SynthesisFailure) as caught:
        NarrationService(provider(runner)).generate(
            text='Hello', voice=reference,
        )
    assert caught.value.measurements == {}
    assert 'secret' not in str(caught.value)


@pytest.mark.parametrize('path', [
    Path('relative'), Path('/x/../y'), Path('/x\ny'),
])
def test_invalid_host_paths_rejected_before_launch(path):
    manifest = Path(__file__).parents[1]/'engines/qwen/model_manifest.json'
    with pytest.raises(ValueError):
        QwenProvider(engine_python=path, model_dir=Path('/approved/models'),
                     manifest=manifest, runner=ControlledRunner())


def test_unapproved_manifest_refused(tmp_path):
    source = Path(__file__).parents[1]/'engines/qwen/model_manifest.json'
    manifest = json.loads(source.read_text())
    manifest['revision'] = 'a' * 40
    altered = tmp_path/'altered.json'
    altered.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='approved pinned'):
        QwenProvider(engine_python=Path('/approved/python'),
                     model_dir=Path('/approved/models'), manifest=altered,
                     runner=ControlledRunner())


def test_unimplemented_settings_and_missing_voice_never_launch(reference):
    runner = ControlledRunner()
    service = NarrationService(provider(runner))
    with pytest.raises(ValueError):
        service.generate(text='Hello', voice=reference, settings={'pace': 1.1})
    with pytest.raises(ValueError):
        service.generate(text='Hello', voice=None)
    assert not runner.calls
