"""Allowlisted diagnostics exclude arbitrary messages and private inputs."""

import json
import logging
from datetime import datetime, timezone
from typing import TextIO


class EventFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", "diagnostic")
        if event not in {
            "config_validated", "config_rejected", "input_rejected",
        }:
            event = "diagnostic"
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": event,
        })


def configure_logging(logger: logging.Logger, stream: TextIO) -> None:
    handler = logging.StreamHandler(stream)
    handler.setFormatter(EventFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
