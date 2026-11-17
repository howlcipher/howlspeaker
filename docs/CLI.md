# CLI and Python API

Install the development branch while its PR is under review:

```bash
git clone --branch feature/wav-export-and-project-page https://github.com/howlcipher/howlspeaker.git
cd howlspeaker
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
howlspeaker --help
```

## Commands

| Command | Behavior |
| --- | --- |
| `howlspeaker config [--config FILE]` | Validate/display JSON safety budgets |
| `howlspeaker validate-voice --voice FILE --authorized --provenance TEXT` | Validate permission attestation and bounded local PCM reference |
| `howlspeaker export-simulation --input FILE --output-dir DIR --name FILE.wav` | Validate/canonicalize PCM, embed simulation label, atomically publish without overwrite |

All commands support `--config FILE`; voice validation additionally supports
`--transcript TEXT` and `--require-transcript`. Exit 0 means that command succeeded;
exit 2 means validation/usage failure. JSON goes to stdout on success; safe errors
go to stderr. Experimental `speak` is the explicit local synthesis entry point;
no HTTP endpoint exists. Help, profiles and the default tests never launch a model.
`sample-script` prints public read-aloud text. `prepare-sample` extracts an
authorized local audio/video clip using the guarded host media service; see
[recording guide](RECORDING.md) for options and Python API examples.
CLI arguments may appear in shell history/process listings; use the Python API
for sensitive provenance or transcript. No raw voice/script logging occurs.

## Validate a voice through Python

```python
from pathlib import Path
from howlspeaker.voice import validate_voice

profile = validate_voice(
    Path("sample.wav"), authorized=True,
    provenance="My recording; I authorize use of my voice",
    transcript="Words spoken in the sample", require_transcript=True,
)
print(profile.audio_metadata())
```

The caller must have permission. The snapshot retains attestation, provenance and
transcript in memory only. Attestation cannot prove speaker identity or consent.
Do not log the profile's private fields. Explicit private storage is available
through ProfileStore and the profile commands; see PROFILES.md.

## Export simulation WAV through Python

```python
from pathlib import Path
from howlspeaker.audio import read_local_audio
from howlspeaker.export import ExportService
from howlspeaker.provider import SimulationResult

fixture = read_local_audio(Path("fixture.wav"), 10 * 1024**2)
report = ExportService().export_simulation(
    SimulationResult(fixture), Path("output"), "check.wav",
)
assert report["evidence_kind"] == "simulation"
```

`output` must already exist. Export accepts validated standard PCM WAV: 8 to 48 kHz,
mono/stereo, integer 8/16/24/32-bit, positive duration up to 30 sec and at most
10 MiB including the embedded simulation label. Configure lower output limits
with Configuration(max_output_bytes=..., max_output_seconds=...). Reference
limits remain independently configurable. Compressed/float/extended WAV and RF64
are unsupported. Metadata is stripped before a new RIFF INFO comment labels the
export as simulation only. PCM samples are preserved, not normalized or enhanced.
A valid silent fixture is not evidence of speech synthesis or quality.

No overwrite is allowed, even for an existing symlink or the original reference.
The service opens each directory component without following symlinks. File
content is flushed before an atomic no-clobber hard-link publication. Ordinary
write/link failures clean temporary files; power-loss directory durability and
hostile same-user directory mutation are not guaranteed. No unsafe fallback on
unsupported filesystems. Successful files are owner-readable/writable (0600).

## Provider seam

`NarrationService.simulate` validates text/consent/reference before one injected
simulation-provider call and returns SimulationResult. Fake providers are defined
only in tests. No production fake is selectable. Deadlines are passed through,
not enforced by the test seam. Real/remote declarations are rejected until a
verified OS-bounded runner exists. Provider metadata is a trusted-code contract,
not a sandbox or proof of model execution.


## Private voice profiles

Use `howlspeaker profile add/list/show/delete`; `--store` and `--config` go before
the action. Explicit profile ID and take ID select one reference, with no global
active speaker. See PROFILES.md for complete CLI/Python examples, default private
location, consent/transcript persistence, deletion and Git exclusions.


## Experimental speak

`howlspeaker speak` selects --voice FILE or --profile ID --take ID, requires
--authorized, --text/--text-file, --out, explicit --engine-python/--model-dir host
paths and the approved --manifest. See SYNTHESIS.md for runnable command/API
recipes and protected runtime installation. Real synthesis and human listening
remain unverified; a controlled fixture is not voice-generation evidence.
