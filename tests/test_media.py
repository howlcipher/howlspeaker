import io
import wave

import pytest

from howlspeaker.cli import main
from howlspeaker.config import Configuration
from howlspeaker.media import MediaImporter, REFERENCE_SCRIPT
from howlspeaker.process import MediaRunResult


class FixtureRunner:
    def __init__(self):
        self.calls = []
        self.result = MediaRunResult(
            b"\0" * 48000, 0, 0.1, 20000000, 0,
        )

    def convert(self, source, arguments, *, max_output_bytes, timeout):
        self.calls.append(
            (source.read(), arguments, max_output_bytes, timeout),
        )
        return self.result


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "source.mp4"
    path.write_bytes(b"synthetic fixture; not real media")
    return path


def prepare(importer, sample, **overrides):
    values = dict(path=sample, authorized=True, provenance="Synthetic fixture",
                  transcript="The words actually spoken", seconds=5)
    values.update(overrides)
    return importer.prepare(**values)


def test_reading_script_cli(capsys):
    assert main(["sample-script"]) == 0
    assert capsys.readouterr().out.strip() == REFERENCE_SCRIPT
    assert 30 <= len(REFERENCE_SCRIPT.split()) <= 65


def test_audio_video_preparation_contract(sample):
    runner = FixtureRunner()
    prepared = prepare(MediaImporter(runner), sample, start=2, audio_stream=1)
    assert prepared.profile.transcript == "The words actually spoken"
    assert prepared.profile.provenance == "Synthetic fixture"
    assert prepared.profile.duration_seconds == 1
    assert prepared.profile.sample_rate == 24000
    assert prepared.profile.channels == 1
    assert prepared.profile.sample_width == 2
    with wave.open(io.BytesIO(prepared.profile.audio_bytes), "rb") as wav:
        assert wav.readframes(24000) == b"\0" * 48000
    assert prepared.measurements["peak_memory_bytes"] == 20000000
    assert len(runner.calls) == 1
    source, args, limit, timeout = runner.calls[0]
    assert source == sample.read_bytes()
    assert args[args.index("-map") + 1] == "0:a:1"
    assert args[args.index("-ss") + 1] == "2.0"
    assert args[args.index("-t") + 1] == "5.0"
    assert "-vn" in args
    assert str(sample) not in args
    assert limit == 5 * 24000 * 2
    assert timeout <= 30
    assert "The words actually spoken" not in repr(prepared)


@pytest.mark.parametrize("values", [
    {"authorized": False}, {"authorized": 1}, {"provenance": ""},
    {"transcript": 1}, {"seconds": 0}, {"seconds": 31},
    {"seconds": float("nan")}, {"start": -1}, {"start": float("inf")},
    {"audio_stream": -1}, {"audio_stream": True}, {"audio_stream": 16},
    {"path": "https://example.org/voice.mp4"},
])
def test_invalid_intake_never_launches(sample, values):
    runner = FixtureRunner()
    with pytest.raises(ValueError):
        prepare(MediaImporter(runner), sample, **values)
    assert not runner.calls


def test_missing_transcript_is_not_invented(sample):
    result = prepare(MediaImporter(FixtureRunner()), sample, transcript=None)
    assert result.profile.transcript is None
    assert result.profile.transcript != REFERENCE_SCRIPT


def test_input_size_rejected_before_decoder(sample):
    runner = FixtureRunner()
    config = Configuration(max_media_bytes=1)
    with pytest.raises(ValueError):
        prepare(MediaImporter(runner, config), sample)
    assert not runner.calls


@pytest.mark.parametrize("payload", [b"", b"x", b"x" * 480001])
def test_empty_unaligned_or_excess_audio_not_accepted(sample, payload):
    runner = FixtureRunner()
    runner.result = MediaRunResult(payload, 0, 0.1, 20000000, 0)
    with pytest.raises(ValueError):
        prepare(MediaImporter(runner), sample)


def test_decoder_failure_is_private(sample):
    runner = FixtureRunner()
    runner.result = MediaRunResult(b"", 1, 0.1, 20000000, 0)
    with pytest.raises(ValueError, match="audio"):
        prepare(MediaImporter(runner), sample)
    assert len(runner.calls) == 1


def test_prepare_cli_publishes_authorized_reference(
    sample, tmp_path, monkeypatch, capsys,
):
    runner = FixtureRunner()
    monkeypatch.setattr("howlspeaker.cli.SystemdMediaRunner",
                        lambda *args, **kwargs: runner)
    transcript = tmp_path / "words.txt"
    transcript.write_text("private spoken words", encoding="utf-8")
    assert main([
        "prepare-sample", "--input", str(sample),
        "--output-dir", str(tmp_path),
        "--name", "reference.wav", "--authorized",
        "--provenance", "my voice",
        "--transcript-file", str(transcript), "--seconds", "5",
    ]) == 0
    import json
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["evidence_kind"] == "authorized_reference"
    assert "private spoken words" not in captured.out + captured.err
    data = (tmp_path / "reference.wav").read_bytes()
    assert b"authorized reference; not generated speech" in data
    assert b"simulation only" not in data


def test_unauthorized_cli_never_reads_transcript(
    sample, tmp_path, monkeypatch, capsys,
):
    def fail(*args):
        pytest.fail("Unauthorized input was read")
    monkeypatch.setattr("howlspeaker.cli.read_local_audio", fail)
    assert main([
        "prepare-sample", "--input", str(sample),
        "--output-dir", str(tmp_path),
        "--name", "reference.wav", "--provenance", "my voice",
        "--transcript-file", str(tmp_path / "private.txt"),
    ]) == 2
    assert "authorization" in capsys.readouterr().err


def test_reference_export_rechecks_authorization(sample, tmp_path):
    from dataclasses import replace
    from howlspeaker.export import ExportService
    profile = prepare(MediaImporter(FixtureRunner()), sample).profile
    with pytest.raises(ValueError):
        ExportService().export_reference(replace(profile, authorized=False),
                                         tmp_path, "reference.wav")
    assert not (tmp_path / "reference.wav").exists()


def test_example_reading_text_matches_cli():
    from pathlib import Path
    assert Path("examples/reference_reading.txt").read_text().strip() \
        == REFERENCE_SCRIPT


@pytest.mark.parametrize("limit", [0, True, 100 * 1024**2 + 1])
def test_invalid_media_size_configuration(limit):
    with pytest.raises(ValueError):
        Configuration(max_media_bytes=limit)
