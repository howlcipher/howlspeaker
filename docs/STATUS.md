# Status

Verified 2026-11-17 UTC.
Current milestone: M1. State: IN PROGRESS; real synthesis acceptance is pending.
M0 remains COMPLETE. No M2+ work started.
Current bounded task: experimental protected Qwen provider and speak CLI/API,
implemented with controlled tests and harmless real-process checks. No real
reference-conditioned synthesis or human listening acceptance is claimed.
Last verified capability: existing sample/profile/simulation/export tools plus
experimental direct-WAV or explicit profile/take speak workflow. Core stays
free of runtime dependencies; ML imports run only in the isolated worker.

Latest full lightweight regression: 290 passed, 0 failed, 0 skipped; flake8 src,
tests and scripts plus JS syntax passed. Added 52 process/provider/worker/CLI/
read-only-artifact cases. The previous 238 tests remain; the obsolete
simulation-only constructor expectation was updated for separate local support,
retaining rejection of remote/unknown kinds and path separation. Wheel build and
installed speak CLI/API checks passed. Test impact: test_impact_synthesis.json.
Real shared-runner media regression and controlled-model/real-library bridge
passed, including timeout/descendant cleanup, private stdout, NaN, overlength,
range and invalid worker request cases. All swap peaks zero. These use synthetic
fixtures, not a model or real voice. See SYNTHESIS.md, synthesis_transport_smoke.json
and synthesis_media_regression.json. No model remains running.

Previous real media smoke remains documented in media_smoke.json. No real voice
or inference smoke ran. CPU load used 1,310,674,944 bytes peak, swap 0, 10.6256s,
exit 0. Download verified 12 files/2,516,104,532 bytes in 26.9689s, peak
2,186,469,376 bytes, swap 0, exit 0. No model processes remain running.
Full setup pins, source URLs, warnings and limits: QWEN_SETUP.md.

Last completed commit before this task: 0608155 (private reusable profiles).
See git log for the current signed protected synthesis implementation commit. Work remains on feature/wav-export-and-project-page
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

Next recommended task: obtain the authorized reference path/transcript/permission
basis, then use the experimental speak/provider workflow for one short real
reference-conditioned CPU smoke within 120 seconds total. Inspect human content
accuracy, intelligibility and voice resemblance separately from WAV validation. If generation fails on time, memory or missing
system dependencies, preserve evidence and stop rather than raise limits/retry.
Acceptance: actual reference used, intelligible playable WAV, measured peak/time/
exit and failure cleanup, relevant unit/integration regression, owner listening.
M1 remains incomplete until all of those pass. No M2+ authorization.
