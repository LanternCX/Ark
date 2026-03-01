"""Runtime logging setup with rich console and rotating files."""

from __future__ import annotations

import logging
import logging.handlers

from rich.console import Console
from rich.logging import RichHandler

from src.runtime_paths import get_runtime_log_path

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5
ACTIVE_LOG_LEVEL = logging.INFO


def get_active_log_level() -> int:
    """Return currently configured console log level."""
    return ACTIVE_LOG_LEVEL


def adopt_dependency_logger(
    name: str, level: int, force_handlers: bool = False
) -> None:
    """Align one dependency logger level and propagation settings."""
    dep_logger = logging.getLogger(name)
    dep_logger.setLevel(level)
    if force_handlers:
        dep_logger.handlers.clear()
        dep_logger.propagate = True


def adopt_dependency_loggers(
    prefixes: tuple[str, ...],
    level: int | None = None,
    force_handlers: bool = False,
) -> None:
    """Align dependency logger levels for prefixes and existing children."""
    effective_level = level if level is not None else get_active_log_level()
    for name in prefixes:
        adopt_dependency_logger(name, effective_level, force_handlers)

    for name, obj in logging.root.manager.loggerDict.items():
        if not isinstance(obj, logging.Logger):
            continue
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            obj.setLevel(effective_level)
            if force_handlers:
                obj.handlers.clear()
                obj.propagate = True


def setup_runtime_logging(level: str = "INFO") -> None:
    """Configure root logging once for Ark runtime sessions."""
    global ACTIVE_LOG_LEVEL
    log_file = get_runtime_log_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    ACTIVE_LOG_LEVEL = resolved_level

    root = logging.getLogger()
    if getattr(root, "_ark_logging_ready", False):
        root.setLevel(logging.DEBUG)
        return

    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
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

    adopt_dependency_loggers(("LiteLLM",), level=logging.WARNING, force_handlers=False)

    root._ark_logging_ready = True  # type: ignore[attr-defined]
