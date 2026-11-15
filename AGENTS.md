# HowlSpeaker agent instructions

Read docs/PRODUCT.md, docs/ROADMAP.md and docs/STATUS.md before changes.
Inspect Git state and confirm the active milestone. Choose one bounded task,
identify affected files and tests, implement it, execute verification, record
evidence and limitations, then update STATUS.md. Stop at the milestone boundary.
Do not redesign architecture without evidence or expand the backlog during work.
Do not begin M2 or later without explicit approval. Do not download models or
perform real inference without approval and verified resource limits.
Do not modify unrelated repositories or run concurrent inference workers.
Default suite is lightweight and offline; real inference must stay opt-in.
Require consent/provenance before voice use and explicit opt-in before uploads.
Never log voice data, scripts, credentials, or arbitrary exception payloads.
No system dependency installation, driver, swap, or kernel changes without approval.
Use documentation/TESTING.md for the final regression gate and impact assessment.
Update README.md and change_log.md before signed Conventional Commits.
