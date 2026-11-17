# Status

Verified 2026-11-17 UTC (live system clock).

Current milestone: M1. State: BLOCKED for real synthesis. M0 remains COMPLETE.
Current bounded task: safe PCM WAV export API/CLI and owner-requested GitHub
backup/project page. Implementation, verification, GitHub backup and live Pages publication complete.
Evidence is recorded in docs/PUBLICATION.md; PR #1 remains OPEN for review.
Last verified capability: script/voice gating, simulation coordination, strict
bounded PCM output validation and labelled atomic no-clobber export. Supported
CLI commands: config, validate-voice, export-simulation. No speak/HTTP endpoint.
Latest full lightweight regression: 147 passed, 0 failed, 0 skipped;
flake8 src tests, JavaScript syntax, wheel build and wheel-installed export passed.
All 114 prior tests remain passing. Desktop/mobile browser QA and visual inspection
passed. No formal accessibility certification claimed.
Last verified implementation commit: 7ae3b75 (project page), with export at
69267b3. MIT/automation bootstrap is ac5841e.
Use git log for current task revision. Foundation backed up on GitHub main;
export/page work is backed up on feature/wav-export-and-project-page in PR #1.
Pages deployment and PR CI passed; public URL/assets returned HTTP 200.
No merge or real-inference completion is claimed.
Known regressions: none observed. Unsupported filesystems fail safely on export.

Next recommended task: implement and verify the OS-bounded subprocess runner
without models, using harmless short-lived children. Acceptance: read back limits,
record duration/exit/peak memory, terminate all descendants on timeout/cancellation,
no retries or unbounded output, and safe actionable errors if enforcement fails.
Code and harmless probes need no model-download approval. No M2 work authorized.

Real synthesis blockers: approved model/dependency download inventory, compatible
isolated runtime and authorized real reference are still needed. CPU duration and
5 GiB peak fit remain unknown; GPU inference compatibility unverified. FFmpeg was
absent on PATH at M0. Downloads, real inference, system dependencies, remote uploads,
paid services and budget increases require explicit approval.
M1 completion still requires intelligible reference-conditioned WAV, resource and
cleanup evidence and human listening. It is not demonstrated.

No model downloads or real inference. Resource measurements remain harmless M0
probes only (BENCHMARKS.md). Export fixtures are silent PCM; playable format does
not establish synthesis or quality. In-process simulation deadlines are not enforced.
Export labels are embedded in WAV and returned JSON; caller-held data are local.
MIT approved by owner; model/dependency licenses remain separate.
Test impact assessment: documentation/TESTING.md, docs/test_impact_export.json
and docs/evidence.jsonl. Public website deploys only site/, never local audio.
