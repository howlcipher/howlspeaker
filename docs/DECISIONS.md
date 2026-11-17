# Decisions

2026-11-15: Start new howlspeaker repository; no existing project found.
Use dependency-free Python CLI foundation. Tradeoffs: ARCHITECTURE.md.
Recommend Qwen3-TTS 0.6B Base provisionally; fallback F5-TTS evaluation only,
with explicit noncommercial weight limitations. No engine is approved to run.
Use CPU as the first investigation path; no supported RX 580 ROCm path verified.
Keep heavy engine dependencies separate from the application environment.
Do not choose an application license on the owner's behalf.
Do not add M1 mock infrastructure merely to imply synthesis is working.
Proceed next with bounded M1 input/consent validation, without downloads.

2026-11-16: Add a structural provider protocol and composition for simulation-only
coordination. Reject real/remote provider declarations until a bounded runner is
implemented and verified. Opaque fixture bytes carry a simulation-only result
label; no WAV, quality or real inference acceptance is inferred. Protocol metadata
is a trusted-code contract, not runtime isolation. Timeout enforcement and output
WAV validation remain separate M1 work, not claimed by this test seam.

2026-11-16: Owner selected MIT licensing matching HowlDream, and authorized GitHub
backup and an ecosystem-style GitHub Pages project page. Keep static site separate
from audio and expose supported functionality via CLI and Python API. No inference
or upload endpoints are exposed. Public repository initialized from signed M0/M1
foundation; export/page changes use a review branch and PR.
Atomic no-clobber hard-link publication was chosen over rename/replace (which
could overwrite an existing target) and over two separate WAV/sidecar writes
(which cannot publish atomically as one pair). Embed the simulation label in WAV.
Fail safely on filesystems without hard-link support. Directory-entry durability
after power loss remains outside the current contract.

2026-11-17: User requested sample footage ingestion plus a read-aloud script and
existing audio/video input. Implement local clip preparation in M1 through CLI/API.
Use existing host FFmpeg under a measured user systemd service; no dependency
installation, model load or original codec implementation. Canonicalize to 24 kHz
mono 16-bit PCM within existing reference limits. Keep an optional user-provided
transcript; never invent one from the script or filename. No live recorder added.
Use a seekable anonymous descriptor to handle regular MP4 files without mapping
project paths across host/container. Separate authorized-reference labels from
simulation labels. Record original source/provenance only in private memory.
