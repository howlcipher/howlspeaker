# Testing

Focused: `python -m pytest tests/test_foundation.py -q`.
Final full lightweight regression: `python -m pytest tests -q` and
`python -m flake8 src tests scripts`. Run serially. Installation acceptance:
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

## Test impact assessment: M1 WAV export and GitHub page

Changed behavior: shared strict PCM validation, independently bounded output,
private atomic no-clobber export with embedded simulation provenance, Python API
and export-simulation CLI. Existing 114 tests still express intended behavior;
retained all of them. Added 33 cases covering playable output, restrictive mode,
embedded label, name/path traversal, directory symlinks, existing-file/reference
preservation, malformed/empty/truncated/overlong data, configured budgets, odd
payload padding, metadata stripping, write/link failures and end-to-end fake
narration to export. No obsolete or duplicate tests removed. Smallest appropriate
tier: unit plus filesystem/CLI and fake-provider integration. Full lightweight
regression required because shared validation and filesystem authority changed.

Manual website verification: cached Chromium, desktop 1440x1000 and mobile 375x812,
no horizontal page overflow or JS errors, persisted theme state, ecosystem menu
Escape/focus behavior and screenshot inspection. No browser/model installation.
Check JS syntax with `node --check site/script.js`. Site has no network services
or uploads. No claim of a formal accessibility audit. Pages and CI must be checked
on GitHub; local tests alone do not prove deployment.

Not exercised: real synthesis, model memory/latency, inference descendant cleanup,
human listening, MP3, normalization or M2+ workflows. An exported silent fixture
is playable PCM but is not a real narration acceptance result.

## Test impact assessment: M1 authorized media preparation

Changed behavior: public read-aloud script and prepare-sample CLI/API; shared
attestation checks, private authorized-reference export and bounded real FFmpeg
media worker. Existing 147 tests remain relevant and passing. Added 44 cases for
script/example consistency, clip selection, track/transcript handoff, no invented
transcript, consent before IO/launch, byte limits, malformed/empty output,
reference-vs-simulation labels, private CLI output, lower-level budgets/metrics,
worker serialization, cancellation/timeout cleanup and fail-closed reports.
No tests removed; no obsolete or duplicate contracts found. Smallest tier: unit
and fake-runner CLI/filesystem integration. Shared validation, process authority
and export changes warrant the complete lightweight gate, plus explicit real
media smoke outside the default suite. No model downloads in any test.

Actual real media smoke: MP3 and MP4 generated tone/video extraction under verified
limits, no-audio video rejection, harmless timeout/descendant cleanup. Record
metrics in docs/media_smoke.json, distinct decoder and audio durations. This smoke
is manual/opt-in, not silently skipped by pytest. Default tests never call host
systemd or FFmpeg. Configured CI now also lints scripts/.

Missing acceptance: real user recordings and human assessment, full codec matrix,
recording devices, persistent voice profile consent records, automatic transcript,
model memory/latency and actual reference-conditioned synthesis. No formal codec
sandbox or audio-quality certification is claimed. No obsolete tests removed.

## Test impact assessment: M1 Qwen setup

Changed behavior: explicit pinned model cache validation/download and guarded
opt-in setup checker. Retained 191 prior contracts; added 25 cases for correct
artifact reuse, corrupt/empty/oversize downloads, invalid manifests, traversal,
symlinks, no-clobber invalid cache, failed transfer cleanup, redirect authority
and exact cgroup budgets before expensive actions. No obsolete or duplicate
tests removed. Smallest tier: unit plus filesystem integration. Existing tests
still express intended behavior. Full lightweight regression is required because
of filesystem/network/resource authority. Engine deps stay outside core runtime.

Actual optional protected checks: dependency install, import, pinned download,
and offline CPU model load. These do not use a voice and are not synthesis tests.
Missing acceptance: reference-conditioned generation, real provider interaction,
its timeout/OOM cleanup and resource costs, intelligibility and human listening.
Neither CPU warning is hidden or counted as a clean synthesis result. No systemd
or network runs in the default suite. No heavy test silently skipped.


## Test impact assessment: M1 private profile takes

Changed behavior: optional persistent consent/audio/transcript snapshots, explicit
speaker/take selection and private CLI add/list/show/delete; export directory
helper can now create private parents only when explicitly requested. Existing
216 tests still express intended behavior, retained unchanged. Added 22 cases
covering private permissions, different speaker/take snapshots, deletion isolation,
consent before IO, default/custom stores, immutable publication, interrupted-link
cleanup, corrupt audio/text/consent/JSON, traversal, symlinks, current audio limits,
bounded reads and Git exclusion of metadata/media. No obsolete or duplicate
contracts removed. Smallest tier: unit plus filesystem and CLI integration.
Shared voice/export helpers and persistence authority warrant full lightweight
regression. Build wheel and exercise installed CLI; site changes are text only,
with unchanged interaction/layout code, checked with existing JS syntax gate.
No new browser/device/model workload. No real profile supplied and no inference
executed; take selection into the real provider and human quality comparison
remain unverified. Hashes detect corruption, never authenticate consent or words.


## Test impact assessment: M1 protected synthesis wiring

Changed behavior: local Qwen adapter/worker, explicit speak CLI with direct WAV
or profile/take selection and fresh authorization, generated-unreviewed export,
shared protected process transport and read-only pinned model verification. Added
52 behavioral cases in test_synthesis, test_speak_cli, test_qwen_worker and the
existing process/model-files suites. Retained all 238 prior cases; updated/renamed
the obsolete simulation-only constructor test to reject remote/unknown kinds
while permitting the distinct local inference path. Simulation never accepts
that path. No tests removed and no duplicate contracts consolidated.

Coverage: actual snapshot/transcript handoff, no raw data in argv/CLI diagnostics,
consent/transcript/script/config/path/model-manifest rejection, selected-profile
isolation, preflight overwrite checks, private failure measurements, total time
and output limits, cgroup/file-size/socket and low-host-memory checks before
imports, cache corruption/symlink/deadline rejection, no retry and disclosure WAV.
Smallest tier: unit, filesystem and controlled provider/CLI integration. Full
lightweight regression warranted because shared resource/export/voice contracts
changed. Gate: pytest tests -q; flake8 src tests scripts; node --check site/script.js;
wheel build and installed CLI/API import checks. No ML dependencies in pytest.

Optional real execution: smoke_media.py rechecks actual host FFmpeg conversions,
no-audio rejection and harmless timeout/descendant cleanup after runner extraction.
smoke_synthesis_transport.py uses the installed CPU audio libraries and a controlled
replacement model to verify bridge/private diagnostics, NaN, overlength and
range rejection, plus actual worker entry-point rejection. Serial only, under
verified budgets. These are distinct opt-in cases, not silently skipped pytest.

Missing acceptance: real Qwen reference encoding/generation/decoding, actual
voice/text matching, actual inference memory/latency, OOM measurements and human
listening. No claim that a mocked return or controlled fixture proves synthesis.
Same-user code/models are trusted and no complete OS/codec sandbox is claimed.
