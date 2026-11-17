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

## 2026-11-17 bounded real media preparation

Host FFmpeg 9.0.2, no GPU, no models, generated test tones/video only.
Reproducible command: `python scripts/smoke_media.py` (explicit opt-in).
Raw measurements and case status: docs/media_smoke.json.

| Case | Decoder wall seconds | Peak cgroup bytes | Swap peak | Exit |
| --- | --- | --- | --- | --- |
| MP3, selected 1 sec | 0.214 | 23187456 | 0 | 0 |
| MP4 video + AAC, selected 1 sec | 0.209 | 24608768 | 0 | 0 |
| Timeout/descendant cleanup | 1.002 | 17260544 | 0 | 124 (expected) |

Output for both conversions: mono 24 kHz 16-bit PCM, 24000 frames (1 second).
Video without an audio track was rejected. Timeout smoke launched harmless
sleeping children and verified the descendant was absent or no longer runnable
after service cleanup. Limits were read back before each conversion, along with
file-size limits and denied IPv4/IPv6 socket creation. There was no OOM test.
These results prove bounded media decoding only, not voice quality, transcription,
model initialization, inference performance or voice cloning.

Initial safe probes exposed an unsupported `RestrictAddressFamilies=none` host
setting; no decoder ran in that failed probe. The compatible AF_UNIX policy was
verified, not silently removed. An initial fixture-generation attempt produced
no data because FFmpeg declined an existing anonymous output descriptor; the
smoke now explicitly writes only that owned descriptor and requires nonempty
fixtures. Failed probes are not counted as successful media acceptance.

## Approved Qwen CPU preparation, 2026-11-17

No real synthesis or voice benchmark. Verified limits stayed 3 GiB high,
5 GiB max, zero swap, 150% CPU, 192 tasks; one job at a time.

| Check | Wall seconds | Peak bytes | Swap peak | Exit |
| --- | --- | --- | --- | --- |
| Dependency setup | 42.245 service | systemd reported 946.3 MB | 0 | 0 |
| Qwen import | 18.653 service | systemd reported 746.5 MB | 0 | 0 |
| Pinned model download/hash check | 26.9689 work | 2186469376 | 0 | 0 |
| Offline CPU BF16/eager model load | 10.6256 work | 1310674944 | 0 | 0 |

All transient services finished and no model remains running. Load is subject to
lazy mapped pages and does not predict generation peak/time. See QWEN_SETUP.md
for exact pins, approval, execution envelope, missing SoX and CPU warnings.


## Protected synthesis implementation checks, 2026-11-17

No real Qwen inference or real reference. The controlled model replacement used
real installed Torch/NumPy/SoundFile, verified the reference tuple/transcript and
CPU/local-only loader arguments, and emitted native/Python diagnostics that were
successfully excluded from binary output. Valid output was a 0.1-second synthetic
fixture. NaN, overlength and out-of-range arrays were rejected without output.
Invalid installed-worker input returned exit 65 without imports or output.

Controlled bridge: 1.8086s, 155172864-byte peak, swap 0, exit 0. Rejected waveform
cases: 1.73–1.80s, peaks below 155 MB, swap 0, expected exit 70. No model was loaded.
See synthesis_transport_smoke.json for final measurements. This is transport and
bridge coverage, never voice-generation acceptance.

Shared media transport rechecked actual MP3/MP4 imports (~0.21s, under 24 MB peak),
no-audio rejection and descendant cleanup on a 1-second timeout (expected exit 124,
1.1271s, 17272832-byte peak). See synthesis_media_regression.json. No OOM stress
test, CPU speech-quality experiment or listening assessment was performed.
