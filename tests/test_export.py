import io
import json
import os
import stat
import wave

import pytest

from howlspeaker.cli import main
from howlspeaker.export import ExportService
from howlspeaker.provider import SimulationResult


def pcm(frames=8000):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setparams((1, 2, 8000, 0, "NONE", "NONE"))
        audio.writeframes(b"\0" * frames * 2)
    return buffer.getvalue()


def test_export_is_playable_private_and_labelled(tmp_path):
    metadata = ExportService().export_simulation(
        SimulationResult(pcm()), tmp_path, "test.wav",
    )
    path = tmp_path / "test.wav"
    with wave.open(str(path), "rb") as audio:
        assert audio.getnframes() == 8000
        assert audio.readframes(8000) == b"\0" * 16000
    label = b"HowlSpeaker: simulation only; not real inference"
    assert label in path.read_bytes()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert metadata["evidence_kind"] == "simulation"
    assert metadata["duration_seconds"] == 1
    assert sorted(item.name for item in tmp_path.iterdir()) == ["test.wav"]


@pytest.mark.parametrize("name", [
    "../escape.wav", "/tmp/escape.wav", "a/b.wav", "a\\b.wav", ".", "..",
    "audio.mp3", ".hidden.wav", "x\0.wav", "x" * 130 + ".wav",
])
def test_unsafe_names_rejected(tmp_path, name):
    with pytest.raises(ValueError):
        ExportService().export_simulation(SimulationResult(pcm()), tmp_path,
                                          name)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("data", [
    b"", b"not wav", pcm()[:-1], pcm(0), pcm(240001),
])
def test_invalid_audio_never_published(tmp_path, data):
    with pytest.raises(ValueError):
        ExportService().export_simulation(SimulationResult(data), tmp_path,
                                          "test.wav")
    assert not list(tmp_path.iterdir())


def test_existing_output_and_symlink_unchanged(tmp_path):
    path = tmp_path / "keep.wav"
    path.write_bytes(b"keep")
    link = tmp_path / "link.wav"
    link.symlink_to(path)
    for name in ("keep.wav", "link.wav"):
        with pytest.raises(ValueError):
            ExportService().export_simulation(
                SimulationResult(pcm()), tmp_path, name,
            )
    assert path.read_bytes() == b"keep"
    assert link.is_symlink()
    assert len(list(tmp_path.iterdir())) == 2


def test_symlink_in_output_directory_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "nested").mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    for directory in (link, link / "nested"):
        with pytest.raises(ValueError):
            ExportService().export_simulation(
                SimulationResult(pcm()), directory, "test.wav",
            )
    assert not list((real / "nested").iterdir())


def test_link_failure_cleans_temporary_file(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("private output path")
    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(ValueError) as error:
        ExportService().export_simulation(SimulationResult(pcm()), tmp_path,
                                          "test.wav")
    assert "private" not in str(error.value)
    assert not list(tmp_path.iterdir())


def test_export_cli(tmp_path, capsys):
    source = tmp_path / "input.wav"
    original = pcm()
    source.write_bytes(original)
    assert main(["export-simulation", "--input", str(source), "--output-dir",
                 str(tmp_path), "--name", "output.wav"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["evidence_kind"] == "simulation"
    assert source.read_bytes() == original
    assert main(["export-simulation", "--input", str(source), "--output-dir",
                 str(tmp_path), "--name", "input.wav"]) == 2
    assert source.read_bytes() == original


def test_wrong_result_type_rejected(tmp_path):
    with pytest.raises(ValueError):
        ExportService().export_simulation(pcm(), tmp_path, "test.wav")


def test_flush_failure_never_publishes(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("private disk error")
    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(ValueError):
        ExportService().export_simulation(SimulationResult(pcm()), tmp_path,
                                          "test.wav")
    assert not list(tmp_path.iterdir())


def test_missing_directory_is_not_created(tmp_path):
    directory = tmp_path / "missing"
    with pytest.raises(ValueError):
        ExportService().export_simulation(SimulationResult(pcm()), directory,
                                          "test.wav")
    assert not directory.exists()


def test_parent_traversal_in_directory_rejected(tmp_path):
    directory = tmp_path / "folder"
    directory.mkdir()
    with pytest.raises(ValueError):
        ExportService().export_simulation(
            SimulationResult(pcm()), directory / "..", "test.wav",
        )
    assert not (tmp_path / "test.wav").exists()


def test_export_limits_include_embedded_label(tmp_path):
    from howlspeaker.config import Configuration
    data = pcm()
    settings = Configuration(max_output_bytes=len(data))
    with pytest.raises(ValueError):
        ExportService(settings).export_simulation(SimulationResult(data),
                                                  tmp_path, "test.wav")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("values", [
    {"max_output_bytes": 0}, {"max_output_bytes": 10 * 1024**2 + 1},
    {"max_output_seconds": 31}, {"max_output_seconds": True},
])
def test_unsafe_export_configuration(values):
    from howlspeaker.config import Configuration
    with pytest.raises(ValueError):
        Configuration(**values)


def test_lower_duration_limit_applies(tmp_path):
    from howlspeaker.config import Configuration
    settings = Configuration(max_output_seconds=1)
    with pytest.raises(ValueError):
        ExportService(settings).export_simulation(SimulationResult(pcm(8001)),
                                                  tmp_path, "test.wav")
    assert not list(tmp_path.iterdir())


def test_odd_pcm_payload_padding_preserved(tmp_path):
    import struct
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setparams((1, 1, 8000, 0, "NONE", "NONE"))
        audio.writeframes(b"\x80" * 8001)
    data = bytearray(stream.getvalue() + b"\0")
    struct.pack_into("<I", data, 4, len(data) - 8)
    ExportService().export_simulation(SimulationResult(bytes(data)), tmp_path,
                                      "odd.wav")
    with wave.open(str(tmp_path / "odd.wav"), "rb") as audio:
        assert audio.readframes(8001) == b"\x80" * 8001


def test_source_metadata_is_not_copied(tmp_path):
    import struct
    # A benign unknown chunk can contain private metadata; retain only PCM.
    data = bytearray(pcm() + b"JUNK\x06\0\0\0secret")
    struct.pack_into("<I", data, 4, len(data) - 8)
    ExportService().export_simulation(SimulationResult(bytes(data)), tmp_path,
                                      "clean.wav")
    assert b"secret" not in (tmp_path / "clean.wav").read_bytes()


def test_narration_snapshot_to_export_integration(tmp_path):
    from howlspeaker.narration import NarrationService

    class FixtureProvider:
        execution_kind = "simulation"
        requires_transcript = False

        def synthesize(self, request):
            assert request.text == "Hello."
            return pcm()

    reference = tmp_path / "reference.wav"
    reference.write_bytes(pcm())
    result = NarrationService(FixtureProvider()).simulate(
        text="Hello.", voice_path=reference, authorized=True,
        provenance="Generated silent fixture",
    )
    report = ExportService().export_simulation(result, tmp_path, "take.wav")
    assert report["evidence_kind"] == "simulation"
    assert report["duration_seconds"] == 1
    assert reference.read_bytes() == pcm()
