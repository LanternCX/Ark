"""Runtime-local path resolution for portable execution."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_runtime_root() -> Path:
    """Return the root directory for runtime-local data."""
    override = os.environ.get("ARK_RUNTIME_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    argv0 = Path(sys.argv[0]).expanduser()
    if argv0.exists() and argv0.is_file():
        return argv0.resolve().parent

    return Path.cwd().resolve()


def get_runtime_data_dir() -> Path:
    """Return runtime data directory under runtime root."""
    return get_runtime_root() / ".ark"


def get_runtime_config_path() -> Path:
    """Return runtime-local config file path."""
    return get_runtime_data_dir() / "config.json"


def get_runtime_logs_dir() -> Path:
    """Return runtime-local logs directory."""
    return get_runtime_data_dir() / "logs"


def get_runtime_log_path() -> Path:
    """Return runtime-local main log file path."""
    return get_runtime_logs_dir() / "ark.log"


def get_runtime_backup_runs_dir() -> Path:
    """Return runtime-local checkpoint directory."""
    return get_runtime_data_dir() / "state" / "backup_runs"


def get_runtime_rules_dir() -> Path:
    """Return runtime-local static rules directory."""
    return get_runtime_root() / "src" / "rules"
