import io
import json
import os
import struct
import wave

import pytest

from howlspeaker.cli import main
from howlspeaker.config import Configuration
from howlspeaker.voice import validate_voice


def wav_bytes(frames=8000, rate=8000, channels=1, width=2):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setparams((channels, width, rate, 0, "NONE", "NONE"))
        audio.writeframes(b"\0" * frames * channels * width)
    return stream.getvalue()


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "voice.wav"
    path.write_bytes(wav_bytes())
    return path


def validate(path, **kwargs):
    return validate_voice(path, authorized=True, provenance="Self recording",
                          **kwargs)


def test_valid_reference_contains_attestation_and_snapshot(sample):
    profile = validate(sample, transcript="Test reference")
    assert profile.duration_seconds == 1
    assert profile.sample_rate == 8000
    assert profile.authorized is True
    assert profile.provenance == "Self recording"
    assert profile.transcript == "Test reference"
    assert profile.audio_bytes == sample.read_bytes()
    sample.write_bytes(b"changed")
    assert profile.audio_bytes.startswith(b"RIFF")
    assert "Self recording" not in repr(profile)
    assert "Test reference" not in repr(profile)


@pytest.mark.parametrize("authorized", [False, None, 1, "yes"])
def test_authority_required_before_file_access(tmp_path, authorized):
    with pytest.raises(ValueError, match="authorization"):
        validate_voice(tmp_path / "absent", authorized=authorized,
                       provenance="Self recording")


@pytest.mark.parametrize("provenance", ["", "   ", None, 123, "x" * 1001])
def test_provenance_required(sample, provenance):
    with pytest.raises(ValueError, match="provenance"):
        validate_voice(sample, authorized=True, provenance=provenance)


def test_transcript_requirement(sample):
    with pytest.raises(ValueError, match="transcript"):
        validate(sample, require_transcript=True)
    assert validate(sample, require_transcript=True,
                    transcript=" Reference ").transcript == "Reference"


@pytest.mark.parametrize("transcript", [123, "x" * 5001])
def test_invalid_transcript(sample, transcript):
    with pytest.raises(ValueError, match="transcript"):
        validate(sample, transcript=transcript)


@pytest.mark.parametrize("data", [
    b"not a wav", wav_bytes()[:-2], wav_bytes(frames=0),
    wav_bytes(rate=7999), wav_bytes(rate=48001),
    wav_bytes(channels=3), wav_bytes(frames=240001),
    wav_bytes() + b"trailing", wav_bytes()[:40] + struct.pack("<I", 15999)
    + b"\0" * 15999 + b"\0",
])
def test_reject_bad_or_unsupported_audio(tmp_path, data):
    path = tmp_path / "bad.wav"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        validate(path)


@pytest.mark.parametrize("channels,width", [(1, 1), (2, 2), (1, 3), (2, 4)])
def test_supported_pcm_formats(tmp_path, channels, width):
    path = tmp_path / "sample.wav"
    path.write_bytes(wav_bytes(channels=channels, width=width))
    assert validate(path).channels == channels


def test_size_limit_and_exact_boundary(sample):
    size = sample.stat().st_size
    assert validate(sample, config=Configuration(max_voice_bytes=size))
    with pytest.raises(ValueError, match="size"):
        validate(sample, config=Configuration(max_voice_bytes=size - 1))


def test_duration_exact_boundary(tmp_path):
    path = tmp_path / "sample.wav"
    path.write_bytes(wav_bytes(frames=240000))
    assert validate(path).duration_seconds == 30


def test_nonregular_paths_rejected_without_blocking(tmp_path, sample):
    link = tmp_path / "link.wav"
    link.symlink_to(sample)
    fifo = tmp_path / "pipe.wav"
    os.mkfifo(fifo)
    for path in (link, fifo, tmp_path, tmp_path / "absent"):
        with pytest.raises(ValueError):
            validate(path)


def test_cli_reports_only_audio_metadata(sample, capsys):
    assert main(["validate-voice", "--voice", str(sample), "--authorized",
                 "--provenance", "private recording"]) == 0
    captured = capsys.readouterr()
    metadata = json.loads(captured.out)
    assert metadata["duration_seconds"] == 1
    assert "private recording" not in captured.out + captured.err
    assert str(sample) not in captured.out + captured.err


def test_cli_rejects_without_authorization(sample, capsys):
    assert main(["validate-voice", "--voice", str(sample),
                 "--provenance", "self"]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "authorization" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("offset,value,encoding", [
    (20, 3, "<H"), (32, 3, "<H"), (28, 1234, "<I"),
    (34, 12, "<H"), (16, 18, "<I"),
])
def test_inconsistent_format_headers_rejected(
    tmp_path, offset, value, encoding,
):
    data = bytearray(wav_bytes())
    struct.pack_into(encoding, data, offset, value)
    path = tmp_path / "bad.wav"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        validate(path)


def test_duplicate_data_chunk_rejected(tmp_path):
    data = bytearray(wav_bytes() + b"data\0\0\0\0")
    struct.pack_into("<I", data, 4, len(data) - 8)
    path = tmp_path / "bad.wav"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        validate(path)


def test_consent_rejection_never_opens_file(sample, monkeypatch):
    def unexpected_open(*args):
        pytest.fail("Unauthorized file was opened")
    monkeypatch.setattr(os, "open", unexpected_open)
    with pytest.raises(ValueError, match="authorization"):
        validate_voice(sample, authorized=False, provenance="self")


def test_cli_malformed_input_has_no_private_details(tmp_path, capsys):
    path = tmp_path / "private.wav"
    path.write_bytes(b"private data")
    assert main(["validate-voice", "--voice", str(path), "--authorized",
                 "--provenance", "private source"]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "private" not in captured.err
    assert "Traceback" not in captured.err
