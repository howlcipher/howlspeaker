"""Explicit local synthesis command, separate from other tools."""

from pathlib import Path

from howlspeaker.audio import read_local_audio
from howlspeaker.export import ExportService
from howlspeaker.narration import NarrationService, validate_script
from howlspeaker.profiles import ProfileStore
from howlspeaker.voice import validate_attestation, validate_voice


def add_speak_parser(commands):
    parser = commands.add_parser(
        'speak', help='Experimental guarded Qwen CPU synthesis',
    )
    reference = parser.add_mutually_exclusive_group(required=True)
    reference.add_argument('--voice', type=Path)
    reference.add_argument('--profile')
    parser.add_argument('--take')
    parser.add_argument('--store', type=Path)
    parser.add_argument('--authorized', action='store_true',
                        help='Confirm permission to clone the selected voice')
    parser.add_argument('--provenance')
    transcript = parser.add_mutually_exclusive_group()
    transcript.add_argument('--transcript')
    transcript.add_argument('--transcript-file', type=Path)
    text = parser.add_mutually_exclusive_group(required=True)
    text.add_argument('--text')
    text.add_argument('--text-file', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--engine-python', type=Path, required=True,
                        help='Absolute host-visible isolated CPU Python path')
    parser.add_argument('--model-dir', type=Path, required=True,
                        help='Absolute host-visible verified model directory')
    parser.add_argument('--manifest', type=Path, required=True,
                        help='Approved pinned manifest, visible to this CLI')
    parser.add_argument('--config', type=Path)


def _read_text(path, limit):
    try:
        return read_local_audio(path, limit).decode('utf-8')
    except (ValueError, UnicodeError):
        raise ValueError('Cannot read bounded UTF-8 text file') from None


def speak(args, config):
    if args.authorized is not True:
        raise ValueError('Explicit voice authorization is required')
    if args.profile is not None:
        if (args.take is None or args.provenance is not None
                or args.transcript is not None
                or args.transcript_file is not None):
            raise ValueError('Select a stored take without metadata overrides')
        voice = ProfileStore(args.store, config).load(args.profile, args.take)
    else:
        if args.take is not None or args.store is not None:
            raise ValueError('Take/store options require profile selection')
        validate_attestation(args.authorized, args.provenance, args.transcript)
        transcript = (args.transcript if args.transcript_file is None else
                      _read_text(args.transcript_file, 20000))
        voice = validate_voice(
            args.voice, authorized=args.authorized, provenance=args.provenance,
            transcript=transcript, require_transcript=True, config=config,
        )
    validate_attestation(True, voice.provenance, voice.transcript,
                         require_transcript=True)
    text = args.text if args.text_file is None else _read_text(
        args.text_file, config.max_script_chars * 4,
    )
    text = validate_script(text, config)
    ExportService.check_destination(args.out.parent, args.out.name)
    from howlspeaker.qwen import QwenProvider
    result = NarrationService(QwenProvider(
        engine_python=args.engine_python, model_dir=args.model_dir,
        manifest=args.manifest, config=config,
    ), config).generate(text=text, voice=voice)
    metadata = ExportService(config).export_generated(
        result, args.out.parent, args.out.name,
    )
    return metadata | dict(
        provider=result.provider_id, model_revision=result.model_revision,
        measurements=result.measurements, configuration=config.to_dict(),
        human_review_required=True,
    )
