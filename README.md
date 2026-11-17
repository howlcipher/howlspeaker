# HowlSpeaker

Local-first narration from authorized voice samples and scripts.
M0 foundation, M1 audio/video sample preparation, voice validation,
simulation coordination, WAV export and private speaker/take profiles are available.
Experimental guarded Qwen synthesis CLI/API is implemented; real voice synthesis
is NOT yet demonstrated. Weights are never bundled or automatically downloaded.

## Install and verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/howlspeaker config
.venv/bin/python -m pytest tests
.venv/bin/python -m flake8 src tests scripts
```

Python 3.12 or newer; M0 verified on 3.14.4 only. Inference needs a separate
compatibility review; upstream recommends Python 3.12. Runtime dependencies:
none. Development dependencies are pinned in pyproject.toml.
`howlspeaker config --config FILE` accepts a JSON object containing a subset
of the displayed defaults. Unknown keys, duplicate keys, unsafe budgets,
and inference enablement are rejected. Config files are limited to 64 KiB.
These budgets do not apply operating-system limits by themselves.

Read docs/STATUS.md, docs/PRODUCT.md and docs/ROADMAP.md before work.
See docs/RESOURCE_SAFETY.md before any expensive operation.
No remote uploads or network listeners. Voice storage is explicit and private;
only the experimental speak command starts a protected local inference worker.
Application code is MIT licensed; model weights retain their own licenses.

## Validate an authorized reference

```bash
howlspeaker validate-voice --voice sample.wav --authorized \
  --provenance "My recording; I authorize use of my voice" \
  --transcript "The words spoken in the reference" --require-transcript
```

Only confirm authorization when you have permission to use the voice.
This command validates a local file and prints audio metadata; it generates no
speech and stores no profile or consent record. API callers receive an immutable
snapshot with provenance and optional transcript. Attestation cannot prove consent
or identity. CLI argument values can appear in shell history and process listings;
use the Python API when reference text or provenance is sensitive.

Supported input: standard RIFF PCM WAV, 8 to 48 kHz, mono/stereo, 8/16/24/32-bit,
positive duration at most 30 seconds and at most 10 MiB including headers.
Configuration may lower these limits. Final-component symlinks, nonregular files,
invalid chunk lengths, duplicate data/format chunks and partial frames are rejected.
Extended/float WAV and RF64 need conversion outside this command. Silence is valid
PCM; intelligibility, speech content and resemblance are not assessed here.
Voice validation copies no source to disk and uploads nothing. Callers must release profile references
to discard in-memory data; secure erasure of Python memory is not guaranteed.

## Provider coordination status

The Python API includes `SynthesisProvider`, private `SynthesisRequest` and
`NarrationService.simulate`. The coordinator validates script length/control
characters, authorization, provenance, transcript requirements and reference WAV
before making one provider call. Generation settings are currently unsupported.
`simulate` accepts only trusted injected simulation providers; fakes are test-only.
The separate `generate` method accepts a local adapter and enforces input/result
validation, with OS limits implemented by the protected worker transport.

`SimulationResult` always labels its opaque bytes as simulation evidence. The coordinator size-checks these bytes. ExportService separately validates PCM
WAV format/duration; neither verifies intelligibility or speech quality.
Provider errors are private and never retried. Timeout budgets are passed through,
not enforced by this in-process test seam. Output size validation occurs after the
provider returns and is not a memory sandbox. No real adapter may use this seam
as a substitute for the verified process/cgroup runner required for inference.
Provider metadata is a trusted-code declaration, not proof of what code executes.

## GitHub automation

Lightweight CI runs unit/integration tests, lint and packaging on pull requests
and main. The Pages workflow publishes only the static `site/` directory, never
voice files, models or local configuration. It can also be manually dispatched
for a reviewed branch. No model downloads or inference run in CI.

## Export labelled simulation audio

```bash
mkdir -p output
howlspeaker export-simulation --input fixture.wav --output-dir output --name check.wav
```

This command validates existing PCM audio and exports it; it does not generate
speech. Exported WAVs include an embedded simulation-only comment and the CLI
returns JSON metadata with `evidence_kind: simulation`. See [CLI and API guide](docs/CLI.md).

Output must be a simple WAV filename in an existing selected directory. Directory
symlinks and traversal are rejected; existing files, links and references cannot
be overwritten. Files are published atomically with mode 0600 using a same-directory
hard link after writing/flushing a private temporary file. Filesystems without
hard-link support fail safely; there is no unsafe overwrite fallback.
Incoming non-audio metadata is stripped. The default output cap is 10 MiB and
30 seconds, including the embedded label. Lower limits through JSON configuration
with `max_output_bytes` and `max_output_seconds`. This is atomic publication,
not a guarantee of directory-entry durability after power loss.

Project page: https://howlcipher.github.io/howlspeaker/
Repository: https://github.com/howlcipher/howlspeaker
The current export/page work is on `feature/wav-export-and-project-page` pending
pull-request review; clone that branch to try these additions before integration.

## Prepare your voice sample

Record the supplied script in your normal voice, or choose an existing authorized
recording, audio file or video with sound. Preparation extracts a selected clip;
it does not generate speech, isolate speakers or verify the transcript.

```bash
mkdir -p samples
howlspeaker sample-script > samples/reference_transcript.txt
# Record yourself reading that exact text, then select your local recording.
howlspeaker prepare-sample --input my-recording.mp4 --authorized \
  --provenance "My recording; I authorize use of my voice" \
  --transcript-file samples/reference_transcript.txt \
  --start 0 --seconds 25 --output-dir samples --name reference.wav
```

For existing footage, supply the words actually spoken in the selected clip;
never substitute the supplied script unless that is what you recorded. Use
`--audio-stream 1` for a second audio track. Default is the first track.
Output is private 24 kHz mono 16-bit PCM WAV, with an authorized-reference label,
not the simulation label. Source files remain unchanged. No automatic transcript.
See [recording and media guide](docs/RECORDING.md) and the public read-aloud text
in [examples/reference_reading.txt](examples/reference_reading.txt).

Requirements: Linux cgroup v2, a working user systemd manager, host Python 3 and
FFmpeg. Existing host tools can be used from Distrobox without installation.
The decoder must pass resource/network checks before touching media; no unrestricted
fallback. Imports are serial, local, at most 100 MiB source and 30 seconds extracted
audio, with a 30-second decoder deadline and explicit cleanup grace periods.
Limits can be lowered. Common self-contained audio/video containers are allowed;
WAV, MP3 and MP4 are verified here. Other codecs depend on your installed FFmpeg.
No models or FFmpeg binaries are bundled. No microphone/camera recorder or HTTP
upload endpoint is implemented; capture with your existing recording application.

## Optional Qwen CPU experiment

The approved isolated Qwen runtime and pinned model files are being checked under
3 GiB soft / 5 GiB hard memory limits with no swap. Core CLI/API stays independent
of the engine. See [setup pins, safeguards and evidence](docs/QWEN_SETUP.md).
Real synthesis is not yet demonstrated. The experimental `speak` command and
`NarrationService.generate` use a protected offline worker. Follow
[the synthesis guide](docs/SYNTHESIS.md) for explicit engine paths, authorized
file/profile selection, limits, measured transport checks and remaining risks.

## Private reusable voice profiles

`howlspeaker profile add/list/show/delete` manages separate speakers and takes.
Profiles default outside the repository, with private permissions and explicit
consent/transcript storage. `ProfileStore.load(profile_id, take)` selects a
revalidated snapshot without global speaker state. In-repo profiles/, voices/,
.howlspeaker/, samples/ and recordings/ are ignored, including their JSON/text.
See [profile commands and API](docs/PROFILES.md) and
[the six-take recording plan](docs/RECORDING.md). Each take uses the same public
[read-aloud script](examples/reference_reading.txt); no automatic merging is claimed.
