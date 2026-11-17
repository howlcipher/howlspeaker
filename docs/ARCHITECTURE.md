# Architecture

Decision: Python package with src layout, argparse, dataclass configuration,
JSON diagnostics and pytest. No runtime dependencies in M0.

| Option | Benefit | Cost | Decision |
| --- | --- | --- | --- |
| Python and argparse | Direct engine ecosystem integration, no CLI dependency | More manual validation/help | Use now |
| Typer or Click | Richer CLI ergonomics | Extra dependencies and compatibility surface | Reconsider with actual need |
| Go application core | Easy standalone distribution | Python inference still needs process boundary | Defer |
| FastAPI and web frontend | Accessible local browser workflow | Server/security/frontend lifecycle | M5 only |
| JSON files | Inspectable portable configuration | No concurrent transactions | Use for small configuration |
| Database | Atomic queries and concurrent updates | Schema/migration overhead | Not needed in M0 |

Foundation modules: config validates immutable safety budgets; diagnostics emits
allowlisted JSON events; cli validates and prints configuration. No model imports.

M1 voice validation implemented: VoiceProfile holds a validated immutable audio
snapshot, authorization attestation, provenance and optional transcript.
`validate_voice` checks authority before reading and bounds reads through a
nonblocking, no-follow regular-file descriptor. Container and PCM metadata checks
precede decoding with standard-library wave. No persistent profile store exists.

M1 provider seam implemented: a structural SynthesisProvider protocol declares
execution kind, transcript requirement and one synthesize(request) method.
SynthesisRequest carries normalized bounded text, the validated immutable voice
snapshot and a timeout budget. NarrationService.simulate rejects real/remote modes,
unsupported settings and invalid inputs before one call. SimulationResult carries
opaque bounded bytes and a fixed simulation evidence label. FakeProvider lives
only in tests; no production implementation or synthesis CLI exists.

Protocol plus composition keeps engines independent with minimal machinery;
unlike a base-class hierarchy it provides no shared implementation. A provider
registry/plugin loader would add discovery and lifecycle complexity without an
installed engine, so neither is introduced. Providers are trusted internal code;
metadata checks are not a security sandbox. Deadline and output byte checks do
not establish process resource protection or playable audio. No inference runner
or automatic retries are implemented.

M1 output validation/export implemented: audio.py shares bounded local reads
and strict PCM/container validation with voice.py. ExportService validates
SimulationResult audio, strips non-audio chunks through standard-library wave,
adds a fixed RIFF INFO simulation comment, then revalidates against independent
output byte/duration limits. CLI `export-simulation` exposes the same API.
Directory-descriptor traversal with O_NOFOLLOW pins the selected directory;
a private temporary file is fsynced before atomic no-clobber hard-link publication.
No sidecar is needed because the label stays inside the WAV; this avoids a
partially published two-file pair. Existing targets are never replaced.

Remaining M1 design: approved real adapter behind an OS-bounded child runner,
measured timeout/failure/descendant cleanup and real-output evidence handling. AudioProcessor uses established libraries/FFmpeg where needed;
ExportService must reject traversal, symlink escapes and reference overwrite.
Keep private files owner-readable and deletable. Introduce these only as needed.
No provider registry, plugin loader, HTTP service, scheduler or database yet.

Public project site: buildless HTML/CSS/JS in site/, separate from private audio.
Uses the Howl shell/navy visual palette, local assets, semantic navigation,
keyboard-accessible theme/ecosystem controls and accurate milestone disclosures.
GitHub Actions deploys only site/ with minimal Pages/OIDC permissions. This
static documentation is not the M5 application interface. No HTTP API added:
CLI and Python endpoints satisfy current scope without server maintenance.

M1 media intake: MediaImporter prepares a bounded authorized clip from a seekable
private source snapshot; SystemdMediaRunner serializes local host conversions,
verifies actual cgroup/file-size/network limits, and invokes established FFmpeg
code for extraction/resampling. No codec/DSP algorithm is reimplemented. Pipe-only
input was rejected as the default because ordinary MP4 files may require seeking;
a private regular descriptor avoids container/host path coupling. A direct
unbounded subprocess would be simpler but cannot provide the required memory and
descendant controls, so there is no such fallback. Host tools are not bundled.
ExportService reuses its existing publisher with a distinct authorized-reference
label; simulation results retain their simulation label. Provenance/transcript
remain private in-memory profile fields. No persistent profile store or recorder.
