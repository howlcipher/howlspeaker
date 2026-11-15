# HowlSpeaker

Local-first narration from authorized voice samples and scripts.
M0 foundation only: configuration and private structured diagnostics work.
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
