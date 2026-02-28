"""Runtime logging setup with rich console and rotating files."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

LOG_DIR = Path.home() / ".ark" / "logs"
LOG_FILE = LOG_DIR / "ark.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def setup_runtime_logging(level: str = "INFO") -> None:
    """Configure root logging once for Ark runtime sessions."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    resolved_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    if getattr(root, "_ark_logging_ready", False):
        root.setLevel(logging.DEBUG)
        return

    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(LOG_FILE),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s",
        )
    )
    root.addHandler(file_handler)

    rich_handler = RichHandler(
        console=Console(stderr=True),
        level=resolved_level,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(rich_handler)

    root._ark_logging_ready = True  # type: ignore[attr-defined]
