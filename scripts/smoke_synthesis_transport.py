"""Opt-in protected transport/bridge smoke, NOT real model synthesis.

Requires the already installed CPU runtime plus the current HowlSpeaker wheel.
Only synthetic audio and a controlled replacement for the model are used.
"""

import argparse
import json
from pathlib import Path
import tempfile

from howlspeaker.audio import validate_pcm_wav
from howlspeaker.config import Configuration
from howlspeaker.process import ProtectedRunner
from howlspeaker.qwen import host_path


BRIDGE = r'''
import io, os, sys, types, wave
from pathlib import Path
import numpy as np
from howlspeaker.config import Configuration
from howlspeaker.voice import validate_snapshot
import howlspeaker.qwen_worker as worker

config = Configuration(max_output_bytes=65536, max_output_seconds=1,
                       timeout_seconds=30)
class ControlledModel:
    @classmethod
    def from_pretrained(cls, path, **kwargs):
        assert path == '/unused-controlled-model'
        assert kwargs['device_map'] == 'cpu'
        assert kwargs['attn_implementation'] == 'eager'
        assert kwargs['local_files_only'] is True
        # Native and Python output must not corrupt the returned WAV.
        os.write(1, b'PRIVATE ENGINE DIAGNOSTIC\n')
        print('PRIVATE PYTHON DIAGNOSTIC', flush=True)
        return cls()

    def generate_voice_clone(self, **kwargs):
        assert kwargs['text'] == 'Controlled transport fixture.'
        assert kwargs['ref_text'] == 'Synthetic reference, not a person.'
        samples, rate = kwargs['ref_audio']
        assert rate == 8000 and samples.shape == (8000,)
        assert samples.dtype == np.float32
        assert kwargs['x_vector_only_mode'] is False
        assert kwargs['max_new_tokens'] == 12
        if sys.argv[1] == 'nan':
            return [np.array([float('nan')], dtype=np.float32)], 24000
        if sys.argv[1] == 'overlength':
            return [np.zeros(24001, dtype=np.float32)], 24000
        if sys.argv[1] == 'out_of_range':
            return [np.array([2.0], dtype=np.float32)], 24000
        return [np.sin(np.arange(2400) * 0.1).astype(np.float32) * 0.1], 24000

sys.modules['qwen_tts'] = types.SimpleNamespace(Qwen3TTSModel=ControlledModel)
source = io.BytesIO()
with wave.open(source, 'wb') as wav:
    wav.setparams((1, 2, 8000, 0, 'NONE', 'NONE'))
    wav.writeframes(b'\0' * 16000)
voice = validate_snapshot(source.getvalue(), authorized=True,
                         provenance='Generated synthetic fixture',
                         transcript='Synthetic reference, not a person.')
worker.decode_request = lambda source: (
    'Controlled transport fixture.', voice,
    Path('/unused-controlled-model'), config,
)
sys.exit(worker.main())
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine-python', type=Path, required=True)
    args = parser.parse_args()
    python = host_path(args.engine_python)
    config = Configuration(max_output_bytes=65536, max_output_seconds=1,
                           timeout_seconds=30)
    runner = ProtectedRunner(config)
    with tempfile.TemporaryFile() as empty:
        bridge = runner.run(empty, [python, '-I', '-c', BRIDGE, 'valid'],
                            max_output_bytes=65536, timeout=30)
    assert bridge.exit_code == 0, bridge.measurements()
    assert b'PRIVATE' not in bridge.output
    audio = validate_pcm_wav(bridge.output, max_bytes=65536, max_seconds=1)
    assert audio['sample_rate'] == 24000 and audio['frames'] == 2400
    with tempfile.TemporaryFile() as empty:
        invalid = runner.run(
            empty, [python, '-I', '-m', 'howlspeaker.qwen_worker'],
            max_output_bytes=65536, timeout=5,
        )
    assert invalid.exit_code == 65 and invalid.output == b''
    cases = [dict(case='controlled_model_real_libraries_bridge',
                  status='PASS', audio=audio, **bridge.measurements()),
             dict(case='installed_worker_rejects_invalid_request',
                  status='PASS', **invalid.measurements())]
    for mode in ('nan', 'overlength', 'out_of_range'):
        with tempfile.TemporaryFile() as empty:
            rejected = runner.run(
                empty, [python, '-I', '-c', BRIDGE, mode],
                max_output_bytes=65536, timeout=30,
            )
        assert rejected.exit_code == 70 and rejected.output == b''
        cases.append(dict(case=mode, status='PASS', **rejected.measurements()))
    print(json.dumps(dict(real_inference=False, real_reference=False,
                          cases=cases), indent=2))


if __name__ == '__main__':
    main()
