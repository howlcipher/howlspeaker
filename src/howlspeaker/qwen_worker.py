"""Private worker entry point. Never import ML libraries outside protection."""

import base64
import io
import json
import os
from pathlib import Path
import resource
import socket
import sys
import time

from howlspeaker.audio import validate_pcm_wav
from howlspeaker.config import Configuration
from howlspeaker.model_files import verify_model
from howlspeaker.narration import validate_script
from howlspeaker.qwen import host_path, validate_manifest
from howlspeaker.voice import validate_snapshot


MAX_REQUEST_BYTES = Configuration().max_voice_bytes * 4 // 3 + 131072


def require_protection(config):
    group = Path('/sys/fs/cgroup') / Path(
        Path('/proc/self/cgroup').read_text().split('0::', 1)[1].strip(),
    ).relative_to('/')
    expected = {
        'memory.high': str(config.memory_high_bytes),
        'memory.max': str(config.memory_max_bytes), 'memory.swap.max': '0',
        'cpu.max': str(config.cpu_quota_percent * 1000) + ' 100000',
        'pids.max': str(config.tasks_max),
    }
    if any((group / key).read_text().strip() != value
           for key, value in expected.items()):
        raise ValueError('Required worker protection is absent')
    memory = dict(line.split(':', 1) for line in
                  Path('/proc/meminfo').read_text().splitlines())
    available = int(memory['MemAvailable'].split()[0]) * 1024
    if available < config.memory_max_bytes:
        raise ValueError('Host memory is below approved budget')
    limit = max(config.max_output_bytes, 16384)
    if resource.getrlimit(resource.RLIMIT_FSIZE) != (limit, limit):
        raise ValueError('Worker file-size protection is absent')
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            connection = socket.socket(family)
        except OSError:
            continue
        connection.close()
        raise ValueError('Worker network denial is absent')


def decode_request(source):
    data = source.read(MAX_REQUEST_BYTES + 1)
    if len(data) > MAX_REQUEST_BYTES:
        raise ValueError('Inference request is too large')
    payload = json.loads(data)
    if type(payload['protocol']) is not int or payload['protocol'] != 1:
        raise ValueError('Unsupported inference protocol')
    config = Configuration(**payload['config'])
    require_protection(config)
    text = validate_script(payload['text'], config)
    voice = validate_snapshot(
        base64.b64decode(payload['audio_base64'], validate=True),
        authorized=payload['authorized'], provenance=payload['provenance'],
        transcript=payload['transcript'], require_transcript=True,
        config=config,
    )
    validate_manifest(payload['manifest'])
    model_dir = Path(host_path(Path(payload['model_dir'])))
    verify_model(payload['manifest'], model_dir,
                 deadline=time.monotonic() + config.timeout_seconds)
    return text, voice, model_dir, config


def _synthesize(text, voice, model_dir, config):
    """The only ML import/load path; called after protection and validation."""
    require_protection(config)
    import importlib.metadata
    if (importlib.metadata.version('qwen-tts') != '0.1.1'
            or importlib.metadata.version('torch') != '2.9.1+cpu'
            or importlib.metadata.version('torchaudio') != '2.9.1+cpu'):
        raise ValueError('Approved CPU engine versions are required')
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    reference, rate = sf.read(io.BytesIO(voice.audio_bytes),
                              dtype='float32', always_2d=True)
    reference = reference.mean(axis=1)
    model = Qwen3TTSModel.from_pretrained(
        str(model_dir), device_map='cpu', dtype=torch.bfloat16,
        attn_implementation='eager', local_files_only=True,
        low_cpu_mem_usage=True, use_safetensors=True,
    )
    waves, output_rate = model.generate_voice_clone(
        text=text, language='Auto', ref_audio=(reference, rate),
        ref_text=voice.transcript, x_vector_only_mode=False,
        max_new_tokens=min(360, config.max_output_seconds * 12),
    )
    if (len(waves) != 1 or type(output_rate) is not int
            or not 8000 <= output_rate <= 48000):
        raise ValueError('Invalid engine output')
    waveform = np.asarray(waves[0])
    if (waveform.ndim != 1 or not 0 < waveform.size
            <= output_rate * config.max_output_seconds
            or not np.isfinite(waveform).all()
            or (np.abs(waveform) > 1).any()):
        raise ValueError('Engine output exceeds audio limits')
    output = io.BytesIO()
    sf.write(output, waveform, output_rate, format='WAV', subtype='PCM_16')
    data = output.getvalue()
    validate_pcm_wav(data, max_bytes=config.max_output_bytes,
                     max_seconds=config.max_output_seconds)
    return data


def main():
    # Own the output descriptor; suppress native and library stdout.
    output = os.dup(sys.stdout.fileno())
    try:
        with open(os.devnull, 'w') as quiet:
            os.dup2(quiet.fileno(), 1)
            os.dup2(quiet.fileno(), 2)
            os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                              HF_HUB_DISABLE_TELEMETRY='1')
            try:
                request = decode_request(sys.stdin.buffer)
            except Exception:
                return 65
            try:
                data = _synthesize(*request)
            except ImportError:
                return 69
            except Exception:
                return 70
            with os.fdopen(output, 'wb', closefd=False) as target:
                target.write(data)
                target.flush()
        return 0
    finally:
        os.close(output)


if __name__ == '__main__':
    sys.exit(main())
