# Recording and local media samples

You can provide an authorized recording of your own voice, an audio file, or
video footage containing an authorized voice. M1 now prepares a local reference;
voice synthesis remains blocked pending approved model setup and real evaluation.
A sample is not identity verification and cannot prove consent by itself.

## Read-aloud script

Run `howlspeaker sample-script` or use examples/reference_reading.txt. The provided
public text is a short natural paragraph intended to fit in a comfortable short
take. Read it in your ordinary voice without imitating another person. If the
recording does not match the text, correct the transcript to the actual speech.

Record in a quiet room with one speaker and little background music. Keep the
microphone at a steady distance. Speak comfortably and preserve natural pauses.
Aim for 10 to 25 seconds; selected output is capped at 30 seconds. Listen to the
take before import. The application currently cannot assess whether the recording
is intelligible, clean, natural, unclipped or suitable for any particular engine.
Use your phone, camera or usual recording app; there is no in-app recorder yet.

## Select your sample

```bash
mkdir -p samples
howlspeaker sample-script > samples/reference_transcript.txt
howlspeaker prepare-sample --input my-recording.mp4 --authorized \
  --provenance "My voice, recorded for this project" \
  --transcript-file samples/reference_transcript.txt \
  --start 0 --seconds 25 --output-dir samples --name reference.wav
```

The same command accepts an audio file instead of a video. `--start` is in seconds,
from 0 through 600. `--seconds` is positive, at most 30 (default 30); it selects a
clip rather than requiring the entire source to be short. The source must be a
regular local file at most 100 MiB. Use an external editor to trim larger footage
before import; the application will not raise limits automatically.

Default track is `--audio-stream 0`, the first audio stream. Select another track
explicitly if your video has multiple audio tracks. This does not isolate one
speaker from mixed voices or music. Choose a clean single-speaker segment first.
Files without audio, unsupported formats, corrupt media or empty selections fail.
A shorter source may yield a shorter clip; inspect the returned duration.

Existing footage requires its actual selected-clip transcript when later needed
by an engine. No STT, transcript guessing, diarization, cleanup or consent inference
is performed. The sample script is never automatically assigned to imported media.
`--transcript-file` reads bounded UTF-8 text; `--transcript` is an alternative.
Text/permission notes can appear in process listings if passed as arguments;
prefer the Python API for sensitive metadata. Do not log VoiceProfile fields.

## API

```python
from pathlib import Path
from howlspeaker.media import MediaImporter
from howlspeaker.export import ExportService

prepared = MediaImporter().prepare(
    path=Path("my-recording.mp4"), authorized=True,
    provenance="My voice, recorded for this project",
    transcript="The words actually spoken in this selected clip",
    start=10, seconds=20, audio_stream=0,
)
report = ExportService().export_reference(
    prepared.profile, Path("samples"), "reference.wav",
)
```

The API returns an immutable voice snapshot with in-memory provenance/transcript
and measured decoder duration, peak cgroup memory, swap peak and exit code.
The CLI returns audio metadata and nested measurements; raw media and transcripts
are not logged. Persisted WAV has a fixed authorized-reference comment, not the
private provenance/transcript or source-video metadata. It is not a registered,
persistent voice profile; retain your transcript/permission records privately.
Delete the prepared file to remove this artifact. No secure erasure is promised.

Output is 24 kHz mono 16-bit PCM WAV, owner read/write (0600), with no video or
incoming metadata. Existing output/reference files cannot be overwritten. The
output directory must already exist and contain no symlink components or `..`.
The same atomic/no-clobber publication used by simulation export applies.

## Decoder safety and compatibility

The existing host user systemd service runs a stdlib Python guard and FFmpeg.
No app source path mapping between Distrobox and host is needed: an unlinked
private seekable input snapshot is passed as a file descriptor, so MP4 metadata
at the end of a file is supported. Only self-contained WAV, MP3, MOV/MP4/M4A,
Matroska/WebM, FLAC, OGG and AAC demuxers are allowed. WAV/MP3/MP4 are verified;
other containers/codecs depend on the installed FFmpeg and remain untested here.
Playlist/network formats and URLs are unsupported. The host FFmpeg binary is not
redistributed; its build and codec licenses remain separate from the MIT app.

Before decoding, the guard reads back all five approved cgroup limits and file
size limits, and verifies IPv4/IPv6 socket creation is denied. A local UNIX socket
family is allowed by the compatible host policy. FFmpeg input protocol/demuxer
allowlists add restrictions. These controls are not a complete codec sandbox.
Decode/filter threads are capped; one application runtime lock prevents concurrent
imports using that runtime directory. No automatic retries or unprotected fallback.

Decoder deadline is min(config timeout, 30 seconds), systemd runtime adds 2 seconds
of cleanup margin, parent launcher wait adds 7 seconds. Control commands have
5-second timeouts and service stop timeout is 2 seconds. Service control-group
cleanup handles descendants; output file size is OS bounded. Temporary input,
output and error snapshots are unlinked private files and closed on completion.
Only fixed safe errors reach the CLI; FFmpeg's raw diagnostics are discarded.
A missing service, incompatible limits or unavailable executable fails closed.
`--ffmpeg` may select a trusted executable visible to the host manager. This is
trusted local configuration, not a user-uploaded plugin interface.

Reproduce the opt-in smoke with `python scripts/smoke_media.py`. It generates only
short test tones and a tiny video, verifies real MP3/MP4 extraction and no-audio
rejection, then checks timeout/descendant cleanup with harmless sleeping children.
It is excluded from the default suite and performs no inference or downloads.
