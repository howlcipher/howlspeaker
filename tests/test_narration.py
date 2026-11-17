import io
import wave

import pytest

from howlspeaker.config import Configuration
from howlspeaker.narration import NarrationService


class FakeProvider:
    """Deterministic fixture, never a production synthesis implementation."""

    execution_kind = "simulation"
    requires_transcript = True

    def __init__(self):
        self.calls = []
        self.output = b"test-only simulated output"
        self.error = None

    def synthesize(self, request):
        self.calls.append(request)
        if self.error:
            raise self.error
        return self.output


@pytest.fixture
def reference(tmp_path):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setparams((1, 2, 8000, 0, "NONE", "NONE"))
        audio.writeframes(b"\0" * 16000)
    path = tmp_path / "voice.wav"
    path.write_bytes(stream.getvalue())
    return path


@pytest.fixture
def provider():
    return FakeProvider()


def run(service, reference, **overrides):
    values = dict(text="Hello, this is a test.", voice_path=reference,
                  authorized=True, provenance="Synthetic fixture",
                  transcript="Reference words")
    values.update(overrides)
    return service.simulate(**values)


def test_valid_inputs_reach_provider_as_private_snapshot(reference, provider):
    result = run(NarrationService(provider), reference)
    assert len(provider.calls) == 1
    request = provider.calls[0]
    assert request.text == "Hello, this is a test."
    assert request.voice.audio_bytes == reference.read_bytes()
    assert request.voice.transcript == "Reference words"
    assert request.timeout_seconds == 120
    assert "Hello" not in repr(request)
    assert "Reference words" not in repr(request)
    assert result.evidence_kind == "simulation"
    assert result.audio_bytes == provider.output
    assert provider.output.decode() not in repr(result)
    with pytest.raises((AttributeError, TypeError)):
        result.evidence_kind = "real_inference"


@pytest.mark.parametrize("text", [
    None, 1, "", " \n\t", "x" * 501, "\0invalid", "bad\x1btext",
])
def test_bad_scripts_do_not_invoke_provider(reference, provider, text):
    with pytest.raises(ValueError):
        run(NarrationService(provider), reference, text=text)
    assert not provider.calls


@pytest.mark.parametrize("overrides", [
    {"authorized": False}, {"authorized": 1}, {"provenance": ""},
    {"transcript": None}, {"transcript": " "},
])
def test_voice_gates_precede_provider(reference, provider, overrides):
    with pytest.raises(ValueError):
        run(NarrationService(provider), reference, **overrides)
    assert not provider.calls


def test_malformed_reference_never_reaches_provider(reference, provider):
    reference.write_bytes(b"not audio")
    with pytest.raises(ValueError):
        run(NarrationService(provider), reference)
    assert not provider.calls


@pytest.mark.parametrize("kind", ["real", "remote", None, 1])
def test_unsupported_provider_kinds_are_blocked(provider, kind):
    provider.execution_kind = kind
    with pytest.raises(ValueError, match="Unsupported provider"):
        NarrationService(provider)
    assert not provider.calls


def test_provider_mode_rechecked_before_invocation(reference, provider):
    service = NarrationService(provider)
    provider.execution_kind = "remote"
    with pytest.raises(ValueError):
        run(service, reference)
    assert not provider.calls


def test_unsupported_settings_rejected(reference, provider):
    with pytest.raises(ValueError, match="settings"):
        run(NarrationService(provider), reference, settings={"pace": 2})
    assert not provider.calls


def test_optional_reference_transcript(reference, provider):
    provider.requires_transcript = False
    run(NarrationService(provider), reference, transcript=None)
    assert provider.calls[0].voice.transcript is None


def test_script_boundary_and_budget_propagation(reference, provider):
    service = NarrationService(provider, Configuration(timeout_seconds=30))
    run(service, reference, text="x" * 500)
    assert provider.calls[0].timeout_seconds == 30


def test_lower_script_limit(reference, provider):
    service = NarrationService(provider, Configuration(max_script_chars=10))
    with pytest.raises(ValueError):
        run(service, reference)
    assert not provider.calls


def test_failure_has_no_retry_or_private_error(reference, provider):
    provider.error = RuntimeError("private transcript or path")
    with pytest.raises(ValueError, match="simulation failed") as error:
        run(NarrationService(provider), reference)
    assert len(provider.calls) == 1
    assert "private" not in str(error.value)


@pytest.mark.parametrize("output", [None, "not bytes", b"", b"x" * 100])
def test_invalid_or_oversized_results(reference, provider, output):
    provider.output = output
    # The reference must fit; constrain the independent output byte ceiling.
    service = NarrationService(provider)
    if isinstance(output, bytes) and output:
        service = NarrationService(provider, max_output_bytes=50)
    with pytest.raises(ValueError):
        run(service, reference)
    assert len(provider.calls) == 1


def test_whitespace_normalization_and_multiline_text(reference, provider):
    run(NarrationService(provider), reference, text="  Hello.\nWorld.  ")
    assert provider.calls[0].text == "Hello.\nWorld."


@pytest.mark.parametrize("limit", [0, -1, 10 * 1024**2 + 1, True, "10"])
def test_unsafe_output_budgets_rejected(provider, limit):
    with pytest.raises(ValueError):
        NarrationService(provider, max_output_bytes=limit)
    assert not provider.calls


@pytest.mark.parametrize("requirement", [None, 1, "yes"])
def test_malformed_provider_capabilities_rejected(provider, requirement):
    provider.requires_transcript = requirement
    with pytest.raises(ValueError):
        NarrationService(provider)
    assert not provider.calls


def test_output_limit_exact_boundary(reference, provider):
    provider.output = b"x" * 50
    result = run(NarrationService(provider, max_output_bytes=50), reference)
    assert len(result.audio_bytes) == 50


def test_no_synthesis_method_is_rejected(provider):
    provider.synthesize = None
    with pytest.raises(ValueError):
        NarrationService(provider)


def test_cannot_supply_real_inference_result(reference, provider):
    provider.output = {
        "audio_bytes": b"test", "evidence_kind": "real_inference",
    }
    with pytest.raises(ValueError):
        run(NarrationService(provider), reference)


def test_simulation_kind_cannot_be_overridden():
    from howlspeaker.provider import SimulationResult
    with pytest.raises(TypeError):
        SimulationResult(b"fixture", evidence_kind="real_inference")


def test_interrupt_is_not_swallowed_or_retried(reference, provider):
    provider.error = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        run(NarrationService(provider), reference)
    assert len(provider.calls) == 1


def test_timeout_is_private_and_not_retried(reference, provider):
    provider.error = TimeoutError("private path")
    with pytest.raises(ValueError) as error:
        run(NarrationService(provider), reference)
    assert "private" not in str(error.value)
    assert len(provider.calls) == 1
