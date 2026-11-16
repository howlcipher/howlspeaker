"""Bounded local PCM references with explicit user attestation."""

import io
import os
import stat
import struct
import wave
from dataclasses import dataclass, field
from pathlib import Path

from howlspeaker.config import Configuration


@dataclass(frozen=True)
class VoiceProfile:
    """Validated snapshot; attestation does not prove identity or permission.

    Private fields are excluded from repr. Profiles are not persisted in M1.
    Future providers must consume this snapshot, never reopen the input path.
    """

    audio_bytes: bytes = field(repr=False)
    provenance: str = field(repr=False)
    transcript: str | None = field(repr=False)
    authorized: bool
    sample_rate: int
    channels: int
    sample_width: int
    frames: int

    @property
    def duration_seconds(self) -> float:
        return self.frames / self.sample_rate

    def audio_metadata(self) -> dict:
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "frames": self.frames,
            "duration_seconds": self.duration_seconds,
        }


def _read_reference(path: Path, limit: int) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Voice reference must be a regular file")
            if info.st_size > limit:
                raise ValueError("Voice reference exceeds size limit")
            data = source.read(limit + 1)
            if len(data) > limit:
                raise ValueError("Voice reference exceeds size limit")
            return data
    except OSError:
        raise ValueError("Cannot read regular local voice reference") from None


def _validate_container(data: bytes) -> None:
    """Reject truncated chunk boundaries otherwise tolerated by wave."""
    if (len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE"
            or struct.unpack_from("<I", data, 4)[0] + 8 != len(data)):
        raise ValueError("Invalid or truncated WAV container")
    position = 12
    kinds = []
    while position < len(data):
        if position + 8 > len(data):
            raise ValueError("Truncated WAV chunk header")
        kind = data[position:position + 4]
        size = struct.unpack_from("<I", data, position + 4)[0]
        start = position + 8
        end = start + size
        if end + size % 2 > len(data):
            raise ValueError("Truncated WAV chunk")
        if kind == b"fmt ":
            if size != 16:
                raise ValueError("Only standard PCM WAV is supported")
            tag, channels, rate, byte_rate, align, bits = struct.unpack_from(
                "<HHIIHH", data, start,
            )
            if (tag != 1 or channels not in (1, 2)
                    or bits not in (8, 16, 24, 32)
                    or not 8000 <= rate <= 48000
                    or align != channels * (bits // 8)
                    or byte_rate != rate * align):
                raise ValueError("Unsupported PCM WAV format")
        if kind in (b"fmt ", b"data"):
            kinds.append(kind)
        position = end + size % 2
    if kinds != [b"fmt ", b"data"]:
        raise ValueError("WAV needs one format and one ordered data chunk")


def validate_voice(
    path: Path, *, authorized: bool, provenance: str,
    transcript: str | None = None, require_transcript: bool = False,
    config: Configuration | None = None,
) -> VoiceProfile:
    """Validate consent before accessing a bounded local file; never infer."""
    if authorized is not True:
        raise ValueError("Explicit voice authorization is required")
    if (not isinstance(provenance, str) or not provenance.strip()
            or len(provenance) > 1000):
        raise ValueError("Voice provenance must contain 1 to 1000 characters")
    if transcript is not None:
        if not isinstance(transcript, str) or len(transcript) > 5000:
            raise ValueError("Reference transcript must be at most 5000 chars")
        transcript = transcript.strip() or None
    if require_transcript and transcript is None:
        raise ValueError("Reference transcript is required")
    settings = config if config is not None else Configuration()
    data = _read_reference(path, settings.max_voice_bytes)
    _validate_container(data)
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            rate = audio.getframerate()
            frames = audio.getnframes()
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            if frames == 0 or frames > settings.max_voice_seconds * rate:
                raise ValueError("Voice duration must be positive and bounded")
            payload = audio.readframes(frames + 1)
            if len(payload) != frames * channels * width:
                raise ValueError("Truncated or unaligned WAV samples")
    except (wave.Error, EOFError, struct.error):
        raise ValueError("Invalid PCM WAV reference") from None
    return VoiceProfile(data, provenance.strip(), transcript, True,
                        rate, channels, width, frames)
