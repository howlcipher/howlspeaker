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

## Test impact assessment: M1 provider coordination

Observable change: simulation-only narration API validates script/reference and
provider contract before one invocation, passes a private snapshot/deadline and
returns bounded bytes with a fixed simulation label. Retained all 71 previous
tests. Added 43 cases covering valid handoff, invalid/edge scripts, required and
optional transcripts, authorization/provenance, malformed reference, unsupported
settings/modes, changed provider declarations, output boundaries, malformed
capabilities, private exceptions, interruption and zero retries. Existing tests
still express intended behavior; no obsolete or duplicate contracts removed.
Smallest tier: unit plus in-process fake-provider integration. The full lightweight
suite and flake8 are the final regression gate. Packaging includes an import check
for the installed service. No heavy tests exist or were skipped silently.

Missing acceptance: output WAV format/duration and atomic export, real engine
execution, timeout/cgroup enforcement, cancellation/descendant cleanup, resource
measurements and human listening. The timeout in a request is not enforcement;
provider mode declarations are not proof of execution or a sandbox.
