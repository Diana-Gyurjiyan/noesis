"""Configure rotating, credential-redacted application logs."""

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


class RedactingFormatter(logging.Formatter):
    """Logging formatter that masks credentials embedded in request URLs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record and redact sensitive query parameters."""
        return re.sub(
            r"(?i)([?&](?:api_key|key|token|access_token)=)[^&\s'\"]+",
            r"\1[REDACTED]",
            super().format(record),
        )


def configure_logging() -> None:
    """Install console and rotating-file handlers for application logs.

    Log files are written under ``backend/logs`` and rotate at two megabytes.
    """
    log_dir = Path(__file__).resolve().parents[2] / "logs"
    log_dir.mkdir(exist_ok=True)
    formatter = RedactingFormatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        log_dir / "paper-radar.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger("paper_radar")
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(console)
        root.addHandler(file_handler)
    root.propagate = False
