"""Bounded local reads and strict standard PCM WAV validation."""

import io
import os
import stat
import struct
import wave
from pathlib import Path


def read_local_audio(path: Path, limit: int) -> bytes:
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


def validate_pcm_wav(
    data: bytes, *, max_bytes: int, max_seconds: int,
) -> dict:
    if not isinstance(data, bytes) or len(data) > max_bytes:
        raise ValueError("Audio exceeds byte limit or is not bytes")
    _validate_container(data)
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            rate = audio.getframerate()
            frames = audio.getnframes()
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            if frames == 0 or frames > max_seconds * rate:
                raise ValueError("Audio duration must be positive and bounded")
            payload = audio.readframes(frames + 1)
            if len(payload) != frames * channels * width:
                raise ValueError("Truncated or unaligned WAV samples")
    except (wave.Error, EOFError, struct.error):
        raise ValueError("Invalid PCM WAV audio") from None
    return {
        "sample_rate": rate, "frames": frames,
        "channels": channels, "sample_width": width,
        "duration_seconds": frames / rate,
    }
