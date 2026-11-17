"""Explicit local CPU adapter. No engine imports or unprotected fallback."""

import base64
import hashlib
import json
from pathlib import Path
import tempfile

from howlspeaker.audio import validate_pcm_wav
from howlspeaker.config import Configuration
from howlspeaker.model_files import load_manifest
from howlspeaker.process import ProtectedRunner, validate_measurements
from howlspeaker.provider import GeneratedResult, SynthesisFailure
from howlspeaker.voice import validate_snapshot


MODEL_REVISION = '5d83992436eae1d760afd27aff78a71d676296fc'
# Pin configs, tokenizers and weights together.
MANIFEST_DIGEST = (
    'bb7bec84569a7bb9f51f296f24391e7cedba12d3f580ad10032f93de578618e3'
)


def validate_manifest(manifest):
    digest = hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(',', ':'),
    ).encode()).hexdigest()
    if digest != MANIFEST_DIGEST:
        raise ValueError('Qwen requires the approved pinned model manifest')


def host_path(path):
    if (not isinstance(path, Path) or not path.is_absolute()
            or '..' in path.parts or len(str(path)) > 4096
            or any(char in str(path) for char in ('\0', '\n', '\r'))):
        raise ValueError('Engine paths must be explicit absolute host paths')
    return str(path)


class QwenProvider:
    execution_kind = 'local_inference'
    requires_transcript = True

    def __init__(self, *, engine_python: Path, model_dir: Path, manifest: Path,
                 config: Configuration | None = None, runner=None):
        self._python = host_path(engine_python)
        self._model_dir = host_path(model_dir)
        self._manifest = load_manifest(manifest)
        validate_manifest(self._manifest)
        self._config = config if config is not None else Configuration()
        self._runner = runner if runner is not None else ProtectedRunner(
            self._config,
        )

    def synthesize(self, request):
        from howlspeaker.narration import validate_script
        text = validate_script(request.text, self._config)
        voice = validate_snapshot(
            request.voice.audio_bytes, authorized=request.voice.authorized,
            provenance=request.voice.provenance,
            transcript=request.voice.transcript, require_transcript=True,
            config=self._config,
        )
        if (type(request.timeout_seconds) is not int
                or not 1 <= request.timeout_seconds
                <= self._config.timeout_seconds):
            raise ValueError('Invalid inference deadline')
        payload = dict(
            protocol=1, text=text, audio_base64=base64.b64encode(
                voice.audio_bytes).decode('ascii'),
            authorized=True, provenance=voice.provenance,
            transcript=voice.transcript, model_dir=self._model_dir,
            manifest=self._manifest, config=self._config.to_dict(),
        )
        command = [self._python, '-I', '-m', 'howlspeaker.qwen_worker']
        with tempfile.TemporaryFile() as source:
            source.write(json.dumps(payload).encode())
            source.seek(0)
            result = self._runner.run(
                source, command,
                max_output_bytes=self._config.max_output_bytes,
                timeout=request.timeout_seconds,
            )
        validate_measurements(result, self._config, request.timeout_seconds)
        measurements = result.measurements()
        if result.exit_code != 0:
            raise SynthesisFailure(measurements)
        try:
            validate_pcm_wav(
                result.output, max_bytes=self._config.max_output_bytes,
                max_seconds=self._config.max_output_seconds,
            )
        except ValueError:
            raise SynthesisFailure(measurements) from None
        return GeneratedResult(result.output, measurements, 'qwen-tts-0.1.1',
                               MODEL_REVISION)
