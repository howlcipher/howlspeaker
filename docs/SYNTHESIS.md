# Experimental bounded local synthesis

M1 implementation is available through `howlspeaker speak` and
`NarrationService.generate`. Real reference-conditioned Qwen synthesis has NOT
been demonstrated. The owner must supply an authorized recording and exact
transcript, then listen to the first bounded result. Neither a fixture nor a
successful model load satisfies M1 acceptance. Do not begin M2+.

## Prerequisites

Use the approved pinned CPU runtime/model from QWEN_SETUP.md. Install the current
HowlSpeaker wheel into that isolated runtime with no dependencies; the parent
CLI remains dependency-free. The existing owner runtime was updated locally
from the wheel without network downloads. On another installation, build the
wheel, then install it with that runtime's package manager. Never install GPU
packages or system tools as an automatic fallback.

Required: Linux cgroup v2, working user systemd, host python3 and trusted isolated
CPython 3.12 with qwen-tts 0.1.1, torch/torchaudio 2.9.1+cpu and the current
HowlSpeaker package. Engine/model paths must be absolute and visible to the host
service, which may differ from Distrobox paths. The CLI's --manifest path is read
in the CLI environment; its contents travel through the private input descriptor.
Only the approved manifest is accepted, including configuration/tokenizer hashes.
All model files are verified read-only in the worker before any model import.
Missing/corrupt files fail without downloads, directory creation or retries.

## Direct reference

Use your complete prepared PCM WAV and its actual UTF-8 transcript:

```bash
mkdir -p output
howlspeaker speak --voice samples/natural_01.wav --authorized \
  --provenance "My own voice; I authorize cloning this recording" \
  --transcript-file samples/reference_transcript.txt \
  --text "Hello, this is a test." --out output/test.wav \
  --engine-python /absolute/host/project/.venv-qwen/bin/python \
  --model-dir /absolute/host/project/models/qwen3_tts_0_6b \
  --manifest engines/qwen/model_manifest.json
```

Replace the host paths explicitly; they are placeholders, not auto-discovery.
`--text-file FILE` accepts a bounded UTF-8 script instead of --text. Use file
options to keep raw text out of process listings/shell history. Script limit is
500 characters. Reference is at most 10 MiB/30 seconds. The same 30-second,
10 MiB output cap includes the final disclosure label; configuration can lower
budgets, never raise them. The output parent must exist; overwrite, traversal
and directory symlinks are rejected. Destination is checked before launching
and publication remains atomic/no-clobber against races.

## Explicit profile/take

```bash
howlspeaker speak --profile speaker_a --take natural_01 --authorized \
  --text-file samples/short_script.txt --out output/test.wav \
  --engine-python /absolute/host/project/.venv-qwen/bin/python \
  --model-dir /absolute/host/project/models/qwen3_tts_0_6b \
  --manifest engines/qwen/model_manifest.json
```

Optional --store selects a custom private profile root. Both IDs are required;
there is no active user to carry over accidentally. This reuses the stored
snapshot/consent/transcript after current-limit validation. Fresh --authorized
is required before cloning, and profile metadata overrides are rejected.
Missing transcripts must be corrected by recording/importing a new take.
No combining takes, automatic quality scoring, emotion controls or fine-tuning.

## Python API

```python
from pathlib import Path
from howlspeaker.export import ExportService
from howlspeaker.narration import NarrationService
from howlspeaker.profiles import ProfileStore
from howlspeaker.qwen import QwenProvider

reference = ProfileStore().load("speaker_a", "natural_01")
provider = QwenProvider(
    engine_python=Path("/absolute/host/project/.venv-qwen/bin/python"),
    model_dir=Path("/absolute/host/project/models/qwen3_tts_0_6b"),
    manifest=Path("engines/qwen/model_manifest.json"),
)
result = NarrationService(provider).generate(
    text="Hello, this is a test.", voice=reference,
)
report = ExportService().export_generated(result, Path("output"), "test.wav")
```

Only invoke with authorization for the selected voice. The stored attestation
is not proof of identity/permission. Reusable local and simulated provider paths
are separate; neither accepts a remote mode. Injected providers/runners are
trusted application code, not a sandbox or evidence that a model was executed.
`GeneratedResult` is always generated_unreviewed; its type alone proves nothing.

## Execution and diagnostics

Media and inference share one nonblocking lock (legacy filename
howlspeaker-media-UID.lock) in the user runtime directory. No waiting queue,
parallel workers or retries. Python -I avoids user-site/PYTHONPATH imports.
The systemd guard reads back all five cgroup budgets, file-size limits and denied
IPv4/IPv6 socket creation. The worker rechecks protection before engine imports and requires host
MemAvailable to cover the approved hard memory budget before artifact reads and
again before model loading. This is a headroom check, not a guarantee against
changes in unrelated workloads.
Default limits remain MemoryHigh=3 GiB, MemoryMax=5 GiB, swap=0, CPUQuota=150%,
TasksMax=192; thread environment variables are 1. HF/Transformers offline and
telemetry-disable settings are explicit. CPU versions are checked before loading.

The 120-second deadline covers worker startup, artifact verification, model
initialization, reference encoding, generation, decoding and WAV validation.
Systemd allows 2 seconds additional cleanup margin, the parent launcher waits up
to timeout+7, and stop/kill control commands have their existing 5-second bounds.
A failed or cancelled worker is stopped as a control group before return; a
remaining owned launcher process group is killed. No unrestricted fallback.
No expensive operation runs during help, profile commands or ordinary imports.

CPU uses BF16/eager/safetensors with local_files_only and low_cpu_mem_usage.
Seed is 0; max_new_tokens is min(360, 12 * max_output_seconds). Other generation
parameters come from the pinned model defaults. A token cap is a safety bound,
not a guarantee that the full script was spoken. BF16 has no native acceleration
on the target Ryzen. Exact reproducibility across libraries/hardware is not
claimed. No pace/emotion parameter is exposed. Upstream SoX absence remains an
unverified inference risk; no system package was installed to suppress it.

Waveform must be finite, mono, within duration and normalized numeric range;
out-of-range samples are rejected rather than silently clipped. SoundFile writes
16-bit PCM; the normal WAV validator checks it again before export. The publisher
strips source metadata, adds a synthetic-speech/human-review label and writes
mode 0600 without clobbering references or existing files.

The worker suppresses both Python/native diagnostics to keep private text and
paths out of logs and to protect binary stdout. Guard stderr carries only fixed
resource fields. Successful CLI JSON includes audio metadata, engine/revision,
measurements, validated budget configuration and human_review_required=true. No transcript/audio/script is printed.
Exit 2 signals failure; when available the safe resource report is retained.
Worker exit 65: request/protection/model verification failed; 69: engine imports
unavailable; 70: initialization/generation/output checks failed; 124: total timeout;
negative signals indicate termination. Errors never trigger an automatic retry.
If the guard itself is killed or cannot report, reject output and explicitly
report metrics unavailable; do not fabricate a zero peak. OOM reporting and real
synthesis resource demands remain untested; no OOM stress test was run.

## Verification boundaries

Default tests use controlled fixtures, not models. Optional
scripts/smoke_synthesis_transport.py --engine-python HOST_PYTHON checks installed
worker rejection and the real NumPy/Torch/SoundFile bridge with a controlled model
replacement, including private diagnostics, NaN, overlength and range failures.
No foundation model or real voice is used. The shared media smoke independently
checks actual systemd timeout/descendant cleanup. Captured metrics are in
synthesis_transport_smoke.json and synthesis_media_regression.json. None is
proof of real voice synthesis or speech quality.

Authoritative adapter API source verified 2026-11-17:
https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/qwen_tts/inference/qwen3_tts_model.py
