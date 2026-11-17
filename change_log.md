# Change log

## 0.1.0 foundation

Added installable dependency-free CLI, strict JSON safety budgets and private
structured diagnostics, baseline tests, engine/environment research and M0/M1
tracking. No voice generation implemented and no model downloads performed.

## M1 bounded voice validation

Added explicit authorization/provenance and optional transcript requirements,
bounded immutable PCM WAV snapshots, private metadata CLI output and authority,
format, truncation, size, duration and filesystem regression coverage.
No engine integration or real synthesis has been performed.

## M1 provider contract and coordination

Added a minimal engine-independent provider protocol, private immutable requests,
explicit simulation results and a simulation-only narration coordinator. Invalid
scripts, authorization, references, unsupported settings and provider modes fail
before invocation. Provider failures are private with zero retries. Added 43
behavioral cases; the fake remains test-only. No real engine or timeout runner.

## Repository foundation

Owner selected MIT licensing. Added lightweight CI and GitHub Pages deployment
workflows with pinned action revisions and no model dependencies.

## M1 WAV export and project page

Added shared strict PCM validation, independent output budgets, simulation-labelled
atomic no-clobber WAV export through the Python API and `export-simulation` CLI.
Strips non-audio metadata, rejects symlink/traversal targets and preserves inputs.
Added export, failure cleanup and narration-to-export regression coverage.
Added a static accessible Howl-style project page with ecosystem links, accurate
milestone labels and working command/API documentation. No inference or uploads.

## Publication evidence

Verified public GitHub backup, MIT license, green CI and successful Pages deployment.
Recorded deployed revision, public HTTP/browser checks and PR review state in
PUBLICATION.md. Export/page changes remain on PR #1; no merge claimed.

## M1 authorized audio and video samples

Added `sample-script`, public reference_reading.txt and recording guidance.
Added `prepare-sample` and MediaImporter for authorized local audio/video excerpts,
transcript files, track selection and 24 kHz mono PCM preparation. Existing host
FFmpeg runs under verified cgroup/file-size/network limits with measured duration,
peak memory and timeout/descendant cleanup. Added separate authorized-reference
export labelling, private artifact ignores, contract tests and opt-in real media
smoke. No speech generation, automatic transcript, recorder or model download.

## Media preparation publication

Backed up the audio/video preparation changes in PR #1, verified green 191-test
GitHub CI and republished the recording instructions to Pages. Checked the public
content and mobile rendering. No merge, model download or synthesis claimed.

## M1 approved Qwen runtime preparation

Added separately pinned CPU engine dependencies, artifact inventory and exact
model manifest. Added bounded sequential size/hash-verified private download
with cache validation, path/redirect protections and no retries. Opt-in setup
checker requires actual cgroup limits and offline loading. Approved isolated
runtime import and model download succeeded; real voice synthesis remains pending.
