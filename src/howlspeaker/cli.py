"""Foundation CLI. No model imports, network requests, or synthesis."""

import argparse
import json
import logging
import sys
from pathlib import Path

from howlspeaker.audio import read_local_audio
from howlspeaker.config import load_configuration
from howlspeaker.export import ExportService
from howlspeaker.provider import SimulationResult
from howlspeaker.diagnostics import configure_logging
from howlspeaker.voice import validate_voice, validate_attestation
from howlspeaker.media import MediaImporter, REFERENCE_SCRIPT
from howlspeaker.process import SystemdMediaRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HowlSpeaker local audio tools",
    )
    parser.add_argument("--version", action="version", version="0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("config", help="Validate and show budgets")
    config.add_argument("--config", type=Path)
    voice = commands.add_parser(
        "validate-voice", help="Check an authorized local PCM WAV reference",
    )
    voice.add_argument("--voice", type=Path, required=True)
    voice.add_argument("--authorized", action="store_true",
                       help="Confirm permission to clone this voice")
    voice.add_argument("--provenance", required=True,
                       help="Describe the source and permission basis")
    voice.add_argument("--transcript")
    voice.add_argument("--require-transcript", action="store_true")
    voice.add_argument("--config", type=Path)
    export = commands.add_parser(
        "export-simulation", help="Validate/export WAV with simulation label",
    )
    export.add_argument("--input", type=Path, required=True)
    export.add_argument("--output-dir", type=Path, required=True)
    export.add_argument("--name", required=True)
    export.add_argument("--config", type=Path)
    commands.add_parser("sample-script", help="Print a read-aloud script")
    prepare = commands.add_parser(
        "prepare-sample", help="Prepare an authorized audio/video clip",
    )
    prepare.add_argument("--input", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--name", required=True)
    prepare.add_argument("--authorized", action="store_true")
    prepare.add_argument("--provenance", required=True)
    text = prepare.add_mutually_exclusive_group()
    text.add_argument("--transcript")
    text.add_argument("--transcript-file", type=Path)
    prepare.add_argument("--start", type=float, default=0)
    prepare.add_argument("--seconds", type=float, default=30)
    prepare.add_argument("--audio-stream", type=int, default=0)
    prepare.add_argument("--ffmpeg", default="ffmpeg")
    prepare.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    if args.command == "sample-script":
        print(REFERENCE_SCRIPT)
        return 0
    logger = logging.getLogger("howlspeaker")
    configure_logging(logger, sys.stderr)
    try:
        settings = load_configuration(args.config)
        if args.command == "prepare-sample":
            validate_attestation(args.authorized, args.provenance,
                                 args.transcript)
            transcript = args.transcript
            if args.transcript_file is not None:
                try:
                    transcript = read_local_audio(
                        args.transcript_file, 20000,
                    ).decode("utf-8")
                except (ValueError, UnicodeError):
                    raise ValueError("Cannot load reference transcript") \
                        from None
            importer = MediaImporter(
                SystemdMediaRunner(settings, ffmpeg=args.ffmpeg), settings,
            )
            prepared = importer.prepare(
                path=args.input, authorized=args.authorized,
                provenance=args.provenance, transcript=transcript,
                start=args.start, seconds=args.seconds,
                audio_stream=args.audio_stream,
            )
            metadata = ExportService(settings).export_reference(
                prepared.profile, args.output_dir, args.name,
            )
            report = metadata | {"measurements": prepared.measurements}
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "export-simulation":
            data = read_local_audio(args.input, settings.max_output_bytes)
            metadata = ExportService(settings).export_simulation(
                SimulationResult(data), args.output_dir, args.name,
            )
            print(json.dumps(metadata, indent=2))
            return 0
        if args.command == "validate-voice":
            profile = validate_voice(
                args.voice, authorized=args.authorized,
                provenance=args.provenance, transcript=args.transcript,
                require_transcript=args.require_transcript, config=settings,
            )
            print(json.dumps(profile.audio_metadata(), indent=2))
            return 0
    except ValueError as error:
        logger.error("", extra={"event": "input_rejected"})
        print(str(error), file=sys.stderr)
        return 2
    logger.info("", extra={"event": "config_validated"})
    print(json.dumps(settings.to_dict(), indent=2))
    return 0
