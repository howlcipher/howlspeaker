# HowlSpeaker

Local-first narration from authorized voice samples and scripts.
M0 foundation and bounded M1 voice validation are available.
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
Application license selection remains an owner decision before public release.

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
No source is copied to disk or uploaded. Callers must release profile references
to discard in-memory data; secure erasure of Python memory is not guaranteed.
