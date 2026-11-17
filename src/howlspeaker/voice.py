"""Bounded local PCM references with explicit user attestation."""

from dataclasses import dataclass, field
from pathlib import Path

from howlspeaker.audio import read_local_audio, validate_pcm_wav
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
    data = read_local_audio(path, settings.max_voice_bytes)
    metadata = validate_pcm_wav(
        data, max_bytes=settings.max_voice_bytes,
        max_seconds=settings.max_voice_seconds,
    )
    return VoiceProfile(
        data, provenance.strip(), transcript, True,
        metadata["sample_rate"], metadata["channels"],
        metadata["sample_width"], metadata["frames"],
    )
