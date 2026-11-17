"""Validate inputs before a single explicitly simulated provider invocation."""

import unicodedata
from pathlib import Path

from howlspeaker.config import Configuration
from howlspeaker.provider import (
    SimulationResult, SynthesisProvider, SynthesisRequest,
)
from howlspeaker.voice import validate_voice


class NarrationService:
    """Simulation-only coordination until a safe inference runner is verified.

    No threads, retries, model loads, exports or remote transports.
    The deadline is passed through; this test seam does not enforce it.
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

    def _check_provider(self) -> None:
        if getattr(self._provider, "execution_kind", None) != "simulation":
            raise ValueError("Only simulation providers are currently allowed")
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
        self._check_provider()
        if settings is not None and (
            not isinstance(settings, dict) or settings
        ):
            raise ValueError("Generation settings are not supported yet")
        if (not isinstance(text, str) or not text.strip()
                or len(text) > self._config.max_script_chars):
            raise ValueError("Script must be nonempty and within size limit")
        if any(unicodedata.category(char) in {"Cc", "Cs"}
               and char not in "\n\r\t" for char in text):
            raise ValueError("Script contains unsupported control characters")
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
