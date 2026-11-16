# Testing

Focused: `python -m pytest tests/test_foundation.py -q`.
Final full lightweight regression: `python -m pytest tests -q` and
`python -m flake8 src tests`. Run serially. Installation acceptance:
editable install with no runtime dependencies, installed `howlspeaker config`,
and wheel build. Heavy inference is not in the default suite and needs explicit
approval, verified limits and real reference audio. There is no heavy test yet.

## Test impact assessment: M0 foundation

Changed behavior: configuration validation, bounded configuration reads,
private diagnostics and CLI success/error behavior. No prior tests existed.
Tests protect safe defaults, valid overrides, unsafe/type/authority rejection,
malformed/non-object/duplicate/unknown JSON, private errors, structured logs,
and CLI success/error integration. These express intended M0 behavior.
Smallest tier: unit plus CLI subprocess integration; full suite is lightweight.
No obsolete/duplicate contracts removed. Missing coverage: real engine inference,
resource timeout/descendant cleanup, voice consent/validation, export and human
listening belong to M1 and remain unverified. Packaging acceptance is executed
outside pytest. Final executed results are recorded in docs/STATUS.md.

## Test impact assessment: M1 voice validation

Observable change: authorize and validate a local reference via API or CLI.
The 32 existing foundation tests remain applicable. Added 39 behavioral cases
cover valid snapshots, authority before IO, provenance/transcript requirements,
format/header consistency, truncation, exact size/duration boundaries, filesystem
special files and CLI private success/failure output. No obsolete tests removed
or duplicate contracts consolidated. Smallest tier: unit and CLI integration.
Fixtures contain generated silent PCM, not real voices or synthesis evidence.
Full lightweight regression and flake8 are required after final code changes.
Missing integration/acceptance: engine receives the actual snapshot; real consent
record persistence/deletion; inference cleanup/resource measurement; export and
human listening. These remain explicitly outside this bounded task.
