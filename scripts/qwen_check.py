"""Opt-in setup checks only, never a substitute for real voice acceptance.

Run inside a protected user systemd service; see docs/QWEN_SETUP.md.
"""

import argparse
import json
import os
from pathlib import Path
import socket
import time

from howlspeaker.model_files import download_model, load_manifest


def verified_cgroup():
    group = Path('/sys/fs/cgroup') / Path(
        Path('/proc/self/cgroup').read_text().split('0::', 1)[1].strip()
    ).relative_to('/')
    expected = {
        'memory.high': '3221225472', 'memory.max': '5368709120',
        'memory.swap.max': '0', 'cpu.max': '150000 100000', 'pids.max': '192',
    }
    if any((group / key).read_text().strip() != value
           for key, value in expected.items()):
        raise ValueError('Required cgroup limits are not enforced')
    return group


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('download', 'load'))
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    group = verified_cgroup()
    manifest = load_manifest(args.manifest)
    started = time.monotonic()
    status = 'FAILED'
    try:
        if args.action == 'download':
            download_model(manifest, args.model_dir)
        else:
            # Rehash before loading; missing files must fail without network.
            for family in (socket.AF_INET, socket.AF_INET6):
                try:
                    connection = socket.socket(family)
                except OSError:
                    continue
                connection.close()
                raise ValueError('Model load requires enforced network denial')
            os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                              HF_HUB_DISABLE_TELEMETRY='1')
            download_model(manifest, args.model_dir)
            import torch
            from qwen_tts import Qwen3TTSModel
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            model = Qwen3TTSModel.from_pretrained(
                str(args.model_dir), device_map='cpu', dtype=torch.bfloat16,
                attn_implementation='eager', local_files_only=True,
                low_cpu_mem_usage=True, use_safetensors=True,
            )
            print(json.dumps({'loaded': type(model).__name__,
                              'torch': torch.__version__,
                              'cuda_available': torch.cuda.is_available()}),
                  flush=True)
        status = 'PASS'
    finally:
        print(json.dumps({
            'action': args.action, 'status': status,
            'duration_seconds': time.monotonic() - started,
            'peak_memory_bytes': int((group / 'memory.peak').read_text()),
            'swap_peak_bytes': int((group / 'memory.swap.peak').read_text()),
        }), flush=True)


if __name__ == '__main__':
    main()
