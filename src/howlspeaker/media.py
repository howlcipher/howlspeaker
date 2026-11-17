"""Authorized audio/video excerpts converted into local PCM references."""

import io
import math
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path

from howlspeaker.audio import read_local_audio, validate_pcm_wav
from howlspeaker.config import Configuration
from howlspeaker.process import SystemdMediaRunner
from howlspeaker.voice import VoiceProfile, validate_attestation


REFERENCE_SCRIPT = (
    "Today I'm recording a short sample of my natural speaking voice. "
    "The morning light filled the room as I opened the window. "
    "I checked the time, picked up a blue notebook, and made a simple plan "
    "for the day. Clear words and comfortable pauses help tell the story."
)


@dataclass(frozen=True)
class PreparedSample:
    profile: VoiceProfile = field(repr=False)
    measurements: dict


class MediaImporter:
    def __init__(self, runner=None, config: Configuration | None = None):
        self._config = config if config is not None else Configuration()
        self._runner = runner if runner is not None else SystemdMediaRunner(
            self._config,
        )

    def prepare(
        self, *, path: Path, authorized: bool, provenance: str,
        transcript: str | None = None, start: float = 0, seconds: float = 30,
        audio_stream: int = 0,
    ) -> PreparedSample:
        provenance, transcript = validate_attestation(
            authorized, provenance, transcript,
        )
        if not isinstance(path, Path):
            raise ValueError("Media input must be a local file path")
        for name, value, lower, upper in (
            ("start", start, 0, 600),
            ("seconds", seconds, 0.01, self._config.max_voice_seconds),
        ):
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not lower <= value <= upper):
                raise ValueError(f"Invalid clip {name}")
        if type(audio_stream) is not int or not 0 <= audio_stream <= 15:
            raise ValueError("Invalid audio stream index")
        data = read_local_audio(path, self._config.max_media_bytes)
        arguments = [
            "-hide_banner", "-nostdin", "-loglevel", "error", "-xerror",
            "-filter_threads", "1", "-threads", "1",
            "-protocol_whitelist", "file",
            "-format_whitelist", "wav,mp3,mov,matroska,webm,flac,ogg,aac",
            "-probesize", "5242880", "-analyzeduration", "5000000",
            "-ss", str(float(start)), "-i", "/proc/self/fd/0",
            "-map", f"0:a:{audio_stream}", "-vn", "-sn", "-dn",
            "-t", str(float(seconds)), "-ac", "1", "-ar", "24000",
            "-c:a", "pcm_s16le", "-threads", "1",
            "-f", "s16le", "pipe:1",
        ]
        with tempfile.TemporaryFile() as source:
            source.write(data)
            source.seek(0)
            result = self._runner.convert(
                source, arguments, max_output_bytes=int(seconds * 24000) * 2,
                timeout=min(30, self._config.timeout_seconds),
            )
        if result.exit_code == 127:
            raise ValueError("FFmpeg is unavailable in the host service")
        if result.exit_code == 124:
            raise ValueError("Media extraction timed out; no output published")
        raw = result.output
        if (result.exit_code != 0 or not isinstance(raw, bytes) or not raw
                or len(raw) % 2 or len(raw) > int(seconds * 24000) * 2):
            raise ValueError("No usable audio; check clip, stream and format")
        output = io.BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setparams((1, 2, 24000, 0, "NONE", "NONE"))
            audio.writeframes(raw)
        wav = output.getvalue()
        metadata = validate_pcm_wav(
            wav, max_bytes=self._config.max_voice_bytes,
            max_seconds=self._config.max_voice_seconds,
        )
        profile = VoiceProfile(
            wav, provenance, transcript, True, metadata["sample_rate"],
            metadata["channels"], metadata["sample_width"], metadata["frames"],
        )
        return PreparedSample(profile, result.measurements())
