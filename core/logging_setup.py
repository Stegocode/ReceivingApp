# Owns: process-wide logging configuration (file handler, format, rotation).
# Must not: read config or environment; contain domain logic; be imported by library modules.
# May import: logging, logging.handlers, pathlib.

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

_STANDARD_LOGRECORD_KEYS = set(logging.makeLogRecord({}).__dict__)


class _ContextFormatter(logging.Formatter):
    """Plain-text formatter that appends extra={} fields as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _STANDARD_LOGRECORD_KEYS and not k.startswith("_")
        }
        base = super().format(record)
        if extras:
            base = f"{base} " + " ".join(f"{k}={v}" for k, v in extras.items())
        return base


def setup_logging(log_dir: Path) -> None:
    """Wire a rotating file handler to the root logger. Call once at application startup."""
    handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "receiving_app.log", when="midnight", backupCount=30
    )
    handler.setFormatter(_ContextFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
