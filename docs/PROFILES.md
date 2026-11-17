# Private voices and multiple takes

Each person gets an opaque profile ID, such as speaker_a. Each recording gets its
own take ID, such as natural_01, natural_02, narration_01 or relaxed_01. IDs use
lowercase letters, digits and underscores, start with a letter, and are at most
32 characters. Do not put personal details in IDs. There is no global active
speaker: select both IDs explicitly. No samples from different users are mixed.

Default storage is $XDG_DATA_HOME/howlspeaker/voices or, when unset,
~/.local/share/howlspeaker/voices. This is outside the repository. Root mode must
be 0700 and snapshot files are 0600. Each JSON snapshot embeds the bounded WAV,
actual transcript, explicit authorization and provenance, creation time, delivery
label, audio and transcript SHA-256. The checksums detect accidental changes,
not malicious edits or consent authenticity. The data is private, not encrypted.
List returns only IDs; show returns technical metadata, labels and checksums,
never raw audio, transcript or permission notes. Listing is bounded to 256 entries.

Git ignores voices/, profiles/, .howlspeaker/, recordings/, samples/ and common
media extensions. The profile folders also cover JSON/text/consent files. Ignore
rules do not remove files previously tracked and can be overridden by force-add.
Never commit personal voice data or logs containing it. Use separate private
stores or operating-system accounts if users need access isolation; named
profiles are not an authentication boundary. GitHub backup is code only.

## CLI

First prepare a clean authorized clip and its actual UTF-8 transcript as described
in RECORDING.md. Add already supported PCM WAV directly:

```bash
howlspeaker profile add --id speaker_a --take natural_01 \
  --voice samples/natural_01.wav --authorized \
  --provenance "My own recording; I authorize cloning my voice" \
  --transcript-file samples/reference_transcript.txt --delivery natural
howlspeaker profile list
howlspeaker profile show --id speaker_a --take natural_01
howlspeaker profile show --id speaker_a --take narration_01
howlspeaker profile delete --id speaker_a --take natural_01
```

Add each take separately with its own ID; show a take only after adding it.
Other users use their own IDs, recordings, transcripts and authorization. For a
custom private location, place --store before the action, for example:
`howlspeaker profile --store /absolute/private/voices list`.
No overwrite: to replace a take, use a new take ID or intentionally delete the old
snapshot. Original recordings/prepared WAVs remain unchanged. Delete removes the
one local stored snapshot, not originals, other takes, backups or secure erasure.
CLI provenance arguments can appear in shell history/process listings; use the
Python API for sensitive metadata. Transcripts can be supplied by bounded file.

## Python selection

```python
from howlspeaker.profiles import ProfileStore

store = ProfileStore()
reference = store.load("speaker_a", "natural_01")
alternate = store.load("speaker_a", "narration_01")
other_user = store.load("speaker_b", "natural_01")
```

Each load returns a revalidated immutable VoiceProfile snapshot under current
limits. These examples require the takes to exist and never create consent on
your behalf. Experimental `speak --profile ID --take ID --authorized` now uses
the selected snapshot; see SYNTHESIS.md. Real generation remains unverified. `store.add(id, take, validated_profile, delivery=...)`
also accepts MediaImporter.prepare(...).profile without exporting an extra WAV.

## What multiple readings mean

Record the same words in three deliveries, preferably two attempts each. Preserve
all takes separately; never glue them into an overlength reference. Duration,
rate/channels/width/frame count and checksums are available now. Delivery is a
user label, not detected emotion, quality or an inference control. Keep subjective
notes privately about clarity, resemblance, pacing and artifacts. Automated
quality scoring/STT remains M4; no M4 work is started here.

Same transcript checksum lets you identify takes intended to share words; it
cannot verify what was actually spoken. Compare under the same microphone,
room, distance and later generation settings. Multiple references support choosing
and comparing takes, not a proven more rounded combined voice or fine-tuning.
Qwen documents a reference clip plus its transcript; list inputs support batching
and do not establish speaker-embedding averaging as a supported application feature.
Source verified 2026-11-17:
https://github.com/QwenLM/Qwen3-TTS/blob/main/qwen_tts/inference/qwen3_tts_model.py
