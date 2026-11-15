"""Foundation CLI. No model imports, network requests, or synthesis."""

import argparse
import json
import logging
import sys
from pathlib import Path

from howlspeaker.config import load_configuration
from howlspeaker.diagnostics import configure_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HowlSpeaker M0 foundation")
    parser.add_argument("--version", action="version", version="0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("config", help="Validate and show budgets")
    config.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    logger = logging.getLogger("howlspeaker")
    configure_logging(logger, sys.stderr)
    try:
        settings = load_configuration(args.config)
    except ValueError as error:
        logger.error("", extra={"event": "config_rejected"})
        print(str(error), file=sys.stderr)
        return 2
    logger.info("", extra={"event": "config_validated"})
    print(json.dumps(settings.to_dict(), indent=2))
    return 0
