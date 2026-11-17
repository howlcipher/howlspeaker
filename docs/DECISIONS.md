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
