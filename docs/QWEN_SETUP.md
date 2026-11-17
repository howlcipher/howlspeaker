# Approved CPU setup

Verified 2026-11-17. Owner approved the isolated engine dependencies, approximately
2.52 GB of model files and one bounded local smoke attempt. Approval does not
extend to larger limits, system packages, drivers, uploads or a paid service.
An authorized real reference and exact transcript are still required for cloning.

## Pinned inputs

Application remains MIT with no core runtime dependencies. Optional engine pins
are separate in engines/qwen/requirements.in and requirements.lock. The lock
contains 88 packages with hashes, including CPU-only torch/torchaudio 2.9.1.
CPython 3.12.14 is isolated in ignored .venv-qwen. No GPU route is enabled.

Qwen code: qwen-tts 0.1.1, Apache-2.0, wheel SHA-256
11a290d8dabc7ef91a90c54478c8ab19b3edb1d85c0882313721892bdc4af15d.
Model: Qwen/Qwen3-TTS-12Hz-0.6B-Base, Apache-2.0, revision
5d83992436eae1d760afd27aff78a71d676296fc. The manifest records every size/hash:
12 files, 2,516,104,532 bytes. Weights are ignored, never committed or uploaded.
Dependency inventory is a download estimate (432,637,787 compressed bytes), not
a completed release license audit. Unspecified transitive license metadata needs
review before distribution. Engine packages and weights are not bundled.

Sources checked 2026-11-17:
* https://github.com/QwenLM/Qwen3-TTS
* https://pypi.org/pypi/qwen-tts/0.1.1/json
* https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/tree/5d83992436eae1d760afd27aff78a71d676296fc
* https://download.pytorch.org/whl/cpu/torch/
* https://download.pytorch.org/whl/cpu/torchaudio/

The pinned manifest downloader has explicit size/hash validation, HTTPS redirect
restrictions, descriptor-based path handling, private atomic no-clobber files,
cache revalidation, a 600-second transfer deadline and no automatic retries.
Interrupted transfers require an explicit new attempt; verified files can be reused.
A corrupt existing artifact fails unchanged rather than being silently replaced.

## Execution envelope

All setup/load jobs use a host user systemd transient service. Before expensive
work, read back memory.high=3221225472, memory.max=5368709120,
memory.swap.max=0, cpu.max="150000 100000", pids.max=192. Fail if different.
Properties: MemoryHigh=3G, MemoryMax=5G, MemorySwapMax=0, CPUQuota=150%,
CPUQuotaPeriodSec=100ms, TasksMax=192, TimeoutStopSec=2, KillMode=control-group,
NoNewPrivileges=yes. Setup/download RuntimeMaxSec is 600/610 seconds respectively;
model load and eventual initialization plus inference have a 120-second ceiling.
No other model runs concurrently. Do not raise these budgets after failure.

Install uses uv pip sync --require-hashes with the lock, concurrency downloads,
builds and installs each 1, HTTP retries 0 and copy link mode. No system changes.
The host must see the project and interpreter paths: Distrobox and host prefixes
can differ. Supply verified host-visible paths explicitly, never assume mapping.

Opt-in tool: scripts/qwen_check.py {download,load} --model-dir PATH --manifest PATH.
It requires the exact cgroup limits and is deliberately outside the normal CLI.
Run it through systemd-run --user --wait --pipe with the above properties,
PYTHONPATH pointing to the project's src directory and the isolated interpreter.
For load also set RestrictAddressFamilies=AF_UNIX, HF_HUB_OFFLINE=1,
TRANSFORMERS_OFFLINE=1, HF_HUB_DISABLE_TELEMETRY=1, and OMP/OPENBLAS/MKL/NUMBA
thread counts to 1. The tool verifies network denial before importing the engine,
rehashes local files, and uses local_files_only, safetensors, CPU, BF16, eager
attention and low_cpu_mem_usage. The parent must enforce its deadline and stop
and inspect the unit after any failure. Never use an unrestricted fallback.

BF16 limits storage but this Ryzen lacks native BF16 acceleration; CPU speed is
unknown. FP32 would roughly double main tensor memory and is not an approved
fallback. FlashAttention is intentionally absent on this CPU route. Import emits
a SoX-not-found warning from upstream dependencies; no executable was installed.
No SoX use appears in qwen_tts source itself; successful import alone cannot
prove that every inference path works without it. Do not install system packages
to suppress warnings. No upstream sample voice is downloaded or cloned.

## Evidence

Dependency service exit 0: 42.245 seconds, reported peak 946.3 MB, swap 0.
Import service exit 0: 18.653 seconds, reported peak 746.5 MB, swap 0;
torch 2.9.1+cpu, CUDA unavailable, Qwen3TTSModel import passed.
Download service exit 0: 26.9689 seconds of work, peak 2,186,469,376 bytes,
swap peak 0; all 12 pinned files verified. Service runtime 27.095 seconds.
Transient download service had already unloaded when cleanup checked it.
These are setup measurements, not synthesis or audio quality evidence.

Offline load service exit 0: 10.6256 seconds work (11.728 seconds service),
peak 1,310,674,944 bytes, swap peak 0. Qwen3TTSModel loaded on CPU with BF16/eager.
Service became inactive/dead and unloaded; no model remains running.
Safetensors pages may be mapped lazily: load peak is not an inference estimate.
Both upstream optional-dependency warnings remained visible. No voice input,
generation, playable narration, speech accuracy or voice resemblance was tested.
