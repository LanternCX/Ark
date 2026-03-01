import logging
from pathlib import Path

from src import runtime_logging


def test_setup_runtime_logging_creates_rotating_log_file(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))

    root = logging.getLogger()
    if hasattr(root, "_ark_logging_ready"):
        delattr(root, "_ark_logging_ready")

    runtime_logging.setup_runtime_logging("INFO")
    logging.getLogger("ark.test").info("hello-log")

    assert (tmp_path / ".ark" / "logs" / "ark.log").exists()


def test_adopt_dependency_loggers_aligns_litellm_loggers() -> None:
    parent = logging.getLogger("LiteLLM")
    child = logging.getLogger("LiteLLM.http_handler")
    parent.setLevel(logging.DEBUG)
    child.setLevel(logging.DEBUG)

    runtime_logging.adopt_dependency_loggers(("LiteLLM",), level=logging.WARNING)

    assert parent.level == logging.WARNING
    assert child.level == logging.WARNING
