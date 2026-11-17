"""Validate input before one simulation or local provider invocation."""

import unicodedata
from pathlib import Path
import re

from howlspeaker.audio import validate_pcm_wav
from howlspeaker.process import MediaRunResult, validate_measurements
from howlspeaker.config import Configuration
from howlspeaker.provider import (
    GeneratedResult, SimulationResult, SynthesisFailure, SynthesisProvider,
    SynthesisRequest,
)
from howlspeaker.voice import VoiceProfile, validate_voice, validate_snapshot


class NarrationService:
    """Separate simulation and local synthesis; no retries or remote transport.

    Local adapters enforce the deadline and resource limits in their worker.
    Simulation only passes a deadline through to controlled test providers.
    """

    def __init__(
        self, provider: SynthesisProvider,
        config: Configuration | None = None, *,
        max_output_bytes: int = 10 * 1024**2,
    ) -> None:
        self._provider = provider
        self._config = config if config is not None else Configuration()
        if (type(max_output_bytes) is not int
                or not 1 <= max_output_bytes <= 10 * 1024**2):
            raise ValueError("Invalid simulation output byte limit")
        self._max_output_bytes = max_output_bytes
        self._check_provider()

    def _check_provider(self, kind=None) -> None:
        current = getattr(self._provider, "execution_kind", None)
        if current not in ("simulation", "local_inference"):
            raise ValueError("Unsupported provider execution kind")
        if kind is not None and current != kind:
            raise ValueError("Provider does not support this execution path")
        requirement = getattr(self._provider, "requires_transcript", None)
        if type(requirement) is not bool:
            raise ValueError("Provider transcript requirement must be boolean")
        if not callable(getattr(self._provider, "synthesize", None)):
            raise ValueError("Provider synthesis contract is missing")

    def simulate(
        self, *, text: str, voice_path: Path, authorized: bool,
        provenance: str, transcript: str | None = None,
        settings: dict | None = None,
    ) -> SimulationResult:
        self._check_provider("simulation")
        if settings is not None and (
            not isinstance(settings, dict) or settings
        ):
            raise ValueError("Generation settings are not supported yet")
        text = validate_script(text, self._config)
        voice = validate_voice(
            voice_path, authorized=authorized, provenance=provenance,
            transcript=transcript,
            require_transcript=self._provider.requires_transcript,
            config=self._config,
        )
        request = SynthesisRequest(text.strip(), voice,
                                   self._config.timeout_seconds)
        try:
            output = self._provider.synthesize(request)
        except Exception:
            # Provider messages can include reference paths or script contents.
            raise ValueError("Provider simulation failed; no retry") from None
        if (not isinstance(output, bytes) or not output
                or len(output) > self._max_output_bytes):
            raise ValueError("Provider returned invalid simulation bytes")
        return SimulationResult(output)

    def generate(self, *, text, voice, settings=None) -> GeneratedResult:
        """One local call; validate WAV before publication."""
        self._check_provider("local_inference")
        if settings is not None and (
                not isinstance(settings, dict) or settings):
            raise ValueError("Generation settings are not supported yet")
        text = validate_script(text, self._config)
        if not isinstance(voice, VoiceProfile):
            raise ValueError("A validated voice snapshot is required")
        voice = validate_snapshot(
            voice.audio_bytes, authorized=voice.authorized,
            provenance=voice.provenance, transcript=voice.transcript,
            require_transcript=self._provider.requires_transcript,
            config=self._config,
        )
        request = SynthesisRequest(text, voice, self._config.timeout_seconds)
        try:
            result = self._provider.synthesize(request)
        except SynthesisFailure as error:
            checked = _checked_report(error.measurements, self._config)
            raise SynthesisFailure(checked.measurements()) from None
        except Exception:
            raise SynthesisFailure() from None
        if (not isinstance(result, GeneratedResult)
                or result.evidence_kind != 'generated_unreviewed'
                or not isinstance(result.provider_id, str)
                or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,64}',
                                    result.provider_id)
                or not isinstance(result.model_revision, str)
                or not re.fullmatch('[a-f0-9]{40}', result.model_revision)):
            raise ValueError('Invalid synthesis result')
        measured = _checked_report(result.measurements, self._config)
        if measured.exit_code != 0:
            raise SynthesisFailure(measured.measurements())
        validate_pcm_wav(result.audio_bytes,
                         max_bytes=self._config.max_output_bytes,
                         max_seconds=self._config.max_output_seconds)
        return result


def validate_script(text, config):
    if (not isinstance(text, str) or not text.strip()
            or len(text) > config.max_script_chars):
        raise ValueError("Script must be nonempty and within size limit")
    if any(unicodedata.category(char) in {"Cc", "Cs"}
           and char not in "\n\r\t" for char in text):
        raise ValueError("Script contains unsupported control characters")
    return text.strip()


def _checked_report(report, config):
    try:
        result = MediaRunResult(b'', **report)
        validate_measurements(result, config, config.timeout_seconds)
        return result
    except (ValueError, TypeError):
        raise SynthesisFailure() from None
