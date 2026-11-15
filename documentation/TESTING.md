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
