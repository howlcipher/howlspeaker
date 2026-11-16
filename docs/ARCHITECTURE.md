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

Remaining M1 design, not implemented: a synthesis workflow validates local reference, attestation,
provenance and optional transcript. A minimal SynthesisProvider accepts text,
reference and supported settings and returns audio plus measurements.
NarrationService coordinates without engine imports. The provider runs in a
bounded child service; do not confuse Python timeouts with memory enforcement.
AudioProcessor validates/converts with established libraries/FFmpeg as needed;
ExportService publishes validated WAV atomically beneath a selected output root.
Reject traversal, symlink escapes, overwrite of references and unsafe subprocess
shell interpolation. Keep private files owner-readable and deletable.
Implement these only when required, with a deterministic test-only fake.
No provider registry, plugin loader, HTTP service, scheduler or database yet.
