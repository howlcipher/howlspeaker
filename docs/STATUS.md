# Status

Verified 2026-11-17 UTC.
Current milestone: M1. State: IN PROGRESS; real synthesis acceptance is pending.
M0 remains COMPLETE. No M2+ work started.
Current bounded task: approved pinned Qwen CPU runtime/download/load feasibility.
Last verified capability: sample-script and authorized audio/video prepare-sample
CLI/Python API plus existing validation, simulation and WAV export. The optional
isolated Qwen runtime now imports and loads the pinned base model offline on CPU.
This is not synthesis evidence and no speak command is advertised yet.

Latest full lightweight regression: 216 passed, 0 failed, 0 skipped; flake8 src,
tests and scripts passed. Added 25 model download/setup guard cases; retained all
191 previous tests. See test_impact_qwen.json and documentation/TESTING.md.
Previous real media smoke remains documented in media_smoke.json. No real voice
or inference smoke ran. CPU load used 1,310,674,944 bytes peak, swap 0, 10.6256s,
exit 0. Download verified 12 files/2,516,104,532 bytes in 26.9689s, peak
2,186,469,376 bytes, swap 0, exit 0. No model processes remain running.
Full setup pins, source URLs, warnings and limits: QWEN_SETUP.md.

Last completed commit before this task: 50d5884. See git log for the current
signed Qwen preparation commit. Work remains on feature/wav-export-and-project-page
in PR #1; no merge. Public static page remains live; PUBLICATION.md records its
verified deployment. No uploads or public synthesis endpoints were introduced.
Known regressions: none in the lightweight suite. Linux user systemd and verified
host-visible tool paths remain required; no unrestricted fallback. Real model
load succeeded but mapped weights and generation may have higher memory demands.

Outstanding blockers: owner-supplied authorized audio/video path, exact words
spoken in the selected clip and permission basis; measured real reference-
conditioned generation; output listening and human assessment. Isolated runtime
and model download approval was given and used. No additional approval needed
for the existing bounded local attempt with an authorized sample. System package
installation, higher budgets, uploads or paid services still require approval.
SoX executable is absent; upstream import warns but model load succeeds.
FlashAttention is intentionally absent for CPU. Transitive unspecified license
metadata still needs release review; the model and engine declare Apache-2.0.

Next recommended task: integrate the real provider through a protected serial
worker and run one short authorized reference-conditioned CPU smoke within the
120-second initialization-plus-generation budget. First obtain the reference
path/transcript/permission basis. If generation fails on time, memory or missing
system dependencies, preserve evidence and stop rather than raise limits/retry.
Acceptance: actual reference used, intelligible playable WAV, measured peak/time/
exit and failure cleanup, relevant unit/integration regression, owner listening.
M1 remains incomplete until all of those pass. No M2+ authorization.
