# HowlSpeaker

Local-first narration from authorized voice samples and scripts.
M0 foundation, M1 voice validation, simulation coordination and WAV export
are available.
Speech generation is not implemented. No weights are bundled or downloaded.

## Install and verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/howlspeaker config
.venv/bin/python -m pytest tests
.venv/bin/python -m flake8 src tests
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
No remote uploads, network listeners, voice storage, or synthesis commands exist.
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
Only trusted injected providers marked `simulation` are accepted. The fake exists
only in tests; there is no fake or real synthesis command in the CLI.

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
