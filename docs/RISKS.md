# Risks

| Risk | Evidence / mitigation | State |
| --- | --- | --- |
| 5 GiB insufficient for engine | No measured peak; bounded smoke only after approval | OPEN |
| CPU too slow | No measured latency; 120 sec timeout | OPEN |
| RX 580 incompatibility | No supported ROCm route verified; use CPU investigation | OPEN |
| Runtime/environment drift | Python 3.14 host versus upstream 3.12 recommendation; isolate and audit dependencies | OPEN |
| Child runtime paths differ | systemd service escapes container cgroup view; verify executable visibility | OPEN |
| Voice misuse/privacy | Future attestation and provenance; local-only, no raw inputs in logs | OPEN |
| Model/dependency licenses | Qwen declarations permissive, F5 weights noncommercial; full dependency review pending | OPEN |
| Misleading fake success | M1 must include real reference-conditioned audio and human listening | CONTROLLED |
| Public release license | Application license not yet selected; no release made | OPEN |
| Audio tooling absent | FFmpeg not on PATH; approval required for system installation | OPEN |
