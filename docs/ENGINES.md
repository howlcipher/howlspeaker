# Engine evaluation

Verified 2026-11-15 from upstream sources below. No weights fetched or models run.
Licensing observations are upstream declarations; dependency review is still needed.

| Criterion | Qwen3-TTS 0.6B Base | F5-TTS v1 Base |
| --- | --- | --- |
| Reference cloning | Audio plus transcript; embedding-only mode available with quality tradeoff [1] | Reference audio and text [3] |
| Code / weights | Apache 2.0 / Apache 2.0 metadata [1,2] | MIT / CC BY NC 4.0 [3,4] |
| Download | Tree 2.52 GB, main tensor 1.83 GB including separate tokenizer directory in tree [2] | Base directory 1.35 GB, additional vocoder/dependencies needed [4,5] |
| Memory | Total peak unknown; 5 GiB fit unverified | Total peak unknown; 5 GiB fit unverified |
| CPU / GPU | CPU investigation pending; upstream examples use CUDA; RX 580 path unverified [1] | CPU selection exists in code; CUDA supported; RX 580 unverified [5] |
| Speed / quality | No local timings or listening; upstream evaluation is not desktop evidence [1] | No local timings or listening; upstream demos are not desktop evidence [3] |
| Integration | Python API, isolate dependencies; use Base for cloning [1] | Python API, vocoder handling, avoid automatic ASR download by supplying transcript [3,5] |
| Maintenance | Official repository and model artifacts available; future support not guaranteed [1,2] | Official repository and model artifacts available; future support not guaranteed [3,4] |

Recommendation: Qwen Base provisionally for permissive declared licenses and
reference-cloning API. F5 is an evaluation fallback only, not an unrestricted
commercial release fallback. No claims about local naturalness or latency yet.
Both require pinned revisions, transitive license review and measured smoke tests.

Capacity estimates, not measurements: reserve at least 8 GiB disk for Qwen
weights, temporary download/cache and environment, and at least 6 GiB for F5;
exact dependency download/install totals unknown. A 0.6B FP32 parameter payload
alone is about 2.4 GB before codec, activations, loader copies and framework.
This lower-bound estimate cannot establish 5 GiB peak fit. Neither engine has
verified memory figures for this CPU. Stop on OOM rather than raise limits.

Local CPU avoids uploads and hardware changes but may be slow or exceed limits.
Local GPU is not justified without supported runtime evidence. An explicitly
configured remote provider could avoid local model memory, but adds privacy,
network, cost and consent requirements. None selected; remote stays disabled.
A supported external machine is another option requiring separate approval.

## Primary sources

[1] https://github.com/QwenLM/Qwen3-TTS

[2] https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/tree/main

[3] https://github.com/SWivid/F5-TTS

[4] https://huggingface.co/SWivid/F5-TTS/tree/main/F5TTS_v1_Base

[5] https://github.com/SWivid/F5-TTS/blob/main/src/f5_tts/infer/utils_infer.py

Repository availability shows maintenance surface, not a future activity promise.
Recheck licenses, revisions and dependency compatibility before installation.
