"""Engine-independent data contract; no engine implementation or imports."""

from dataclasses import dataclass, field
from typing import Protocol

from howlspeaker.voice import VoiceProfile


@dataclass(frozen=True)
class SynthesisRequest:
    text: str = field(repr=False)
    voice: VoiceProfile = field(repr=False)
    timeout_seconds: int


class SynthesisProvider(Protocol):
    """Trusted injected code, not a sandbox or dynamically loaded plugin.

    Current orchestration accepts only simulation providers. Real adapters
    must enforce deadlines and OS limits in an isolated process runner.
    """

    @property
    def execution_kind(self) -> str: ...

    @property
    def requires_transcript(self) -> bool: ...

    def synthesize(self, request: SynthesisRequest) -> bytes: ...


@dataclass(frozen=True)
class SimulationResult:
    """Opaque fixture bytes, never real inference or audio-quality evidence."""

    audio_bytes: bytes = field(repr=False)
    evidence_kind: str = field(default="simulation", init=False)
