"""Private, no-clobber atomic publication of labelled simulation WAV files."""

import io
import os
import re
import struct
import uuid
import wave
from pathlib import Path

from howlspeaker.audio import validate_pcm_wav
from howlspeaker.config import Configuration
from howlspeaker.provider import SimulationResult
from howlspeaker.voice import VoiceProfile, validate_attestation


SIMULATION_LABEL = b"HowlSpeaker: simulation only; not real inference\0"


def _open_directory(path: Path) -> int:
    """Pin an existing output directory without following any symlink."""
    if ".." in path.parts:
        raise ValueError("Output directory traversal is not supported")
    descriptor = os.open(path.anchor or ".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        parts = path.parts[1:] if path.anchor else path.parts
        for part in parts:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _labelled_wav(data: bytes, label: bytes = SIMULATION_LABEL) -> bytes:
    """Retain PCM samples, stripping incoming metadata before labelling."""
    output = io.BytesIO()
    with wave.open(io.BytesIO(data), "rb") as source:
        with wave.open(output, "wb") as destination:
            destination.setparams(source.getparams())
            destination.writeframes(source.readframes(source.getnframes()))
    canonical = output.getvalue()
    # RIFF chunks have even-byte padding; wave omits it for odd data payloads.
    if len(canonical) % 2:
        canonical += b"\0"
    comment = b"ICMT" + struct.pack("<I", len(label))
    comment += label + b"\0" * (len(label) % 2)
    info = b"INFO" + comment
    labelled = canonical + b"LIST" + struct.pack("<I", len(info)) + info
    return labelled[:4] + struct.pack("<I", len(labelled) - 8) + labelled[8:]


class ExportService:
    def __init__(self, config: Configuration | None = None) -> None:
        self._config = config if config is not None else Configuration()

    def export_simulation(
        self, result: SimulationResult, output_dir: Path, name: str,
    ) -> dict:
        if (not isinstance(result, SimulationResult)
                or result.evidence_kind != "simulation"):
            raise ValueError("Only labelled simulation results are allowed")
        return self._export(result.audio_bytes, output_dir, name,
                            SIMULATION_LABEL, "simulation")

    def export_reference(
        self, profile: VoiceProfile, output_dir: Path, name: str,
    ) -> dict:
        if not isinstance(profile, VoiceProfile):
            raise ValueError("A validated voice profile is required")
        validate_attestation(profile.authorized, profile.provenance,
                             profile.transcript)
        return self._export(
            profile.audio_bytes, output_dir, name,
            b"HowlSpeaker: authorized reference; not generated speech\0",
            "authorized_reference", reference=True,
        )

    def _export(
        self, data: bytes, output_dir: Path, name: str,
        label: bytes, evidence_kind: str, *, reference: bool = False,
    ) -> dict:
        if (not isinstance(name, str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.wav",
                                name) is None):
            raise ValueError("Output name must be a simple WAV filename")
        limits = dict(
            max_bytes=(self._config.max_voice_bytes if reference
                       else self._config.max_output_bytes),
            max_seconds=(self._config.max_voice_seconds if reference
                         else self._config.max_output_seconds),
        )
        validate_pcm_wav(data, **limits)
        labelled = _labelled_wav(data, label)
        metadata = validate_pcm_wav(labelled, **limits)
        descriptor = None
        temporary = ".howlspeaker-" + uuid.uuid4().hex + ".tmp"
        created = False
        try:
            descriptor = _open_directory(output_dir)
            file_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                              | os.O_NOFOLLOW, 0o600, dir_fd=descriptor)
            created = True
            with os.fdopen(file_fd, "wb") as target:
                target.write(labelled)
                target.flush()
                os.fsync(target.fileno())
            # Link is atomic and fails if any destination already exists.
            os.link(temporary, name, src_dir_fd=descriptor,
                    dst_dir_fd=descriptor, follow_symlinks=False)
        except OSError:
            raise ValueError("Cannot publish WAV; check directory and name") \
                from None
        finally:
            if descriptor is not None:
                try:
                    if created:
                        os.unlink(temporary, dir_fd=descriptor)
                except OSError:
                    raise ValueError("Cannot clean temporary export file") \
                        from None
                finally:
                    os.close(descriptor)
        return metadata | {"evidence_kind": evidence_kind, "filename": name}
