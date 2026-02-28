import logging
from pathlib import Path

from ark import runtime_logging


def test_setup_runtime_logging_creates_rotating_log_file(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(runtime_logging, "LOG_DIR", tmp_path)
    monkeypatch.setattr(runtime_logging, "LOG_FILE", tmp_path / "ark.log")

    root = logging.getLogger()
    if hasattr(root, "_ark_logging_ready"):
        delattr(root, "_ark_logging_ready")

    runtime_logging.setup_runtime_logging("INFO")
    logging.getLogger("ark.test").info("hello-log")

    assert (tmp_path / "ark.log").exists()
