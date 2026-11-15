# Benchmarks and evidence

2026-11-15: No inference benchmark. No downloaded weights, no voice sample,
no real synthesis, no quality/voice-resemblance result.
Harmless systemd probe: true service 16 ms, memory peak 1.2 MB, swap 0,
exit 0. Child cgroup inspection service: 32 ms, peak 2.9 MB, swap 0, exit 0.
These prove budget configuration, not model fit or OOM/descendant cleanup behavior.

Future benchmark record: engine and revision; dependencies; CPU/device/dtype;
reference hash and consent record (keep raw voice private); script fixture;
seed/settings; cgroup limits; wall duration; memory/swap peak; exit status;
audio format/duration; human text accuracy and resemblance assessment.
Keep measurements separate from listening judgments. Later sets: conversation,
technical terms, punctuation/paragraphs and long narration, at their milestones.
