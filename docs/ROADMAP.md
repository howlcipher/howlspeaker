# Roadmap

| Gate | Objective | Exit evidence | State |
| --- | --- | --- | --- |
| M0 | Feasibility and foundation | Installed skeleton, baseline tests, engine/fallback recommendation, risks and next step | COMPLETE |
| M1 | Minimum viable voice generation | Real playable intelligible WAV from authorized reference; actual reference use; measured resources; cleanup; tests | BLOCKED |
| M2 | Reliable narration pipeline | Multi-paragraph output with independently verified ordering and completeness | NOT STARTED |
| M3 | Naturalness and selective editing | Sentence replacement preserves surrounding audio, with listening comparisons | NOT STARTED |
| M4 | Audio quality verification | Controlled defects trigger documented warnings and limitations | NOT STARTED |
| M5 | Local user interface | Full narration workflow through localhost UI | NOT STARTED |
| M6 | Optional integrations and release | Fresh installation, supported workflow, security/license review and reproducible artifacts | NOT STARTED |

M1 acceptance: explicit consent and provenance; local bounded PCM WAV input
at most 10 MiB and 30 seconds; transcript supplied when required; short script
at most 500 characters (first smoke: “Hello, this is a test.”); one worker,
zero retries, at most 120 seconds total initialization and synthesis.
Actual model receives reference and transcript. Output must be nonempty PCM WAV
with valid sample rate/channels and positive bounded duration. Record model
revision, configuration, exit code, wall time, cgroup peak and swap usage.
A human must listen for content and voice resemblance; fake audio is insufficient.
Failure, timeout and cancellation must kill the whole process group/cgroup and
leave no published partial output. Lightweight regression must pass.

M2 requires ordered segmentation, stitching, format consistency, normalization,
bounded retries, recovery and missing/duplicate detection. M3 investigates pace,
pauses, pronunciation, sentence repair, breaths, artifacts and smooth transitions.
M4 adds STT comparison, missing/repeated words, silence, clipping, format checks
and machine-readable reports with human flags. M5 provides import, script edit,
profiles, generation, playback, regeneration, export and visible errors.
M6 includes install/developer docs, consent/privacy, dependency/license and security
review, known limitations and release tests. All integrations remain optional.
Do not begin M2 through M6 without owner approval. No milestone scope changes.

Owner-directed M1 input addition, 2026-11-17: provide a read-aloud reference script
and accept recorded voice, existing audio files and video sound tracks through
local selected-clip preparation. This expands reference import formats without
changing M1's real-synthesis exit gate or authorizing M2+. Sample preparation,
resource readback and decoder cleanup require their own evidence. In-app recording
and automatic transcription are not part of this bounded task.
