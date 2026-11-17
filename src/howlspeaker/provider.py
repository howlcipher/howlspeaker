"""Engine-independent contracts and private results; no inference imports."""

from __future__ import annotations

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

    Simulation and local inference have separate orchestration paths. Local
    adapters enforce deadlines and OS limits in an isolated process runner.
    """

    @property
    def execution_kind(self) -> str: ...

    @property
    def requires_transcript(self) -> bool: ...

    def synthesize(
        self, request: SynthesisRequest,
    ) -> bytes | GeneratedResult: ...


@dataclass(frozen=True)
class SimulationResult:
    """Opaque fixture bytes, never real inference or audio-quality evidence."""

    audio_bytes: bytes = field(repr=False)
    evidence_kind: str = field(default="simulation", init=False)


@dataclass(frozen=True)
class GeneratedResult:
    """Adapter-reported synthesis, always requiring human review.

    The type does not prove that an injected provider used a model.
    """

    audio_bytes: bytes = field(repr=False)
    measurements: dict
    provider_id: str
    model_revision: str
    evidence_kind: str = field(default="generated_unreviewed", init=False)


class SynthesisFailure(ValueError):
    """Fixed private error with validated measurements, when available."""

    def __init__(self, measurements: dict | None = None):
        self.measurements = measurements if measurements is not None else {}
        reason = {
            65: "request, protection or pinned model check failed",
            69: "CPU engine dependencies unavailable",
            70: "engine initialization or generation failed",
            124: "initialization and synthesis timed out",
            -9: "worker killed; inspect resource report",
        }.get(self.measurements.get('exit_code'), "local worker failed")
        super().__init__("Synthesis failed: " + reason + "; no retry")
