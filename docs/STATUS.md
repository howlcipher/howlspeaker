# Status

Verified 2026-11-17 UTC.
Current milestone: M1. State: BLOCKED for real synthesis. M0 remains COMPLETE.
Current bounded task: owner-directed authorized audio/video sample ingestion and
read-aloud script, implemented and locally verified. No M2+ work started.
Last verified capability: sample-script CLI; prepare-sample CLI/Python API extracts
a selected audio/video sound track into a private authorized-reference WAV;
existing validation, simulation and export remain passing.
Full lightweight regression: 191 passed, 0 failed, 0 skipped. Lint includes
src/, tests/ and scripts/. Real media smoke passes MP3, MP4, no-audio rejection
and timeout/descendant cleanup. Peaks/durations/exit statuses in BENCHMARKS.md
and media_smoke.json. This is media decoding, not inference evidence.
Last completed commit before this task: 55f01e6 (GitHub publication evidence).
Current work remains on feature/wav-export-and-project-page in PR #1; no merge.
See git log and PR checks for final head. Website publication evidence is in
PUBLICATION.md; updated media guidance is prepared for the next deployment.
Known regressions: none in the lightweight suite. Linux user systemd and compatible
host tools are required; no unrestricted fallback. Other codec combinations are
untested. No in-app microphone/camera recorder or HTTP upload endpoint exists.

Next recommended task: prepare a pinned Qwen CPU dependency/download inventory
and executable smoke proposal using the existing resource guard pattern. Verify
exact engine/model revisions, dependencies, licenses, download/storage estimates
and whether the approved budget is plausible before requesting model approval.
Acceptance: a concrete reproducible short reference-conditioned smoke plan with
bounded runtime, result validation, measurements and cleanup; no surprise downloads.
Inventory/research needs no download approval. Weights/dependencies, real inference,
system installation, uploads, costs or budget increases need explicit approval.

Real synthesis blockers: approved model/dependency inventory/download, compatible
isolated runtime and an authorized real reference. CPU speed and 5 GiB model fit
remain unknown; RX 580 GPU compatibility unverified. Host FFmpeg is available even
though it is absent from the container PATH. No install was performed.
M1 completion still requires intelligible reference-conditioned WAV, measured
resource/failure cleanup evidence and human listening. It is not demonstrated.

No model downloads or real inference. Sample source files stay local and unchanged.
Prepared WAV contains only canonical PCM and a fixed authorized-reference label;
private provenance/transcript are retained in memory, not logged or persisted.
The read-aloud script is never assigned as an existing-file transcript by default.
Public site remains static documentation, with no voice upload or model endpoint.
Test impact assessment: documentation/TESTING.md and docs/test_impact_media.json.
