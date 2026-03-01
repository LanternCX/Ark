from pathlib import Path
import sys

from src import runtime_paths


def test_runtime_root_prefers_env_override(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))

    assert runtime_paths.get_runtime_root() == tmp_path.resolve()


def test_runtime_root_uses_script_directory(monkeypatch, tmp_path: Path) -> None:
    script = tmp_path / "main.py"
    script.write_text("print('ark')\n", encoding="utf-8")

    monkeypatch.delenv("ARK_RUNTIME_ROOT", raising=False)
    monkeypatch.setattr(sys, "argv", [str(script)])

    assert runtime_paths.get_runtime_root() == tmp_path.resolve()


def test_runtime_root_falls_back_to_cwd_when_argv_is_not_a_file(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("ARK_RUNTIME_ROOT", raising=False)
    monkeypatch.setattr(sys, "argv", ["ark"])
    monkeypatch.chdir(tmp_path)

    assert runtime_paths.get_runtime_root() == tmp_path.resolve()


def test_runtime_paths_are_below_runtime_data_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ARK_RUNTIME_ROOT", str(tmp_path))

    assert runtime_paths.get_runtime_data_dir() == tmp_path / ".ark"
    assert runtime_paths.get_runtime_config_path() == tmp_path / ".ark" / "config.json"
    assert runtime_paths.get_runtime_logs_dir() == tmp_path / ".ark" / "logs"
    assert (
        runtime_paths.get_runtime_log_path() == tmp_path / ".ark" / "logs" / "ark.log"
    )
    assert runtime_paths.get_runtime_backup_runs_dir() == (
        tmp_path / ".ark" / "state" / "backup_runs"
    )
    assert runtime_paths.get_runtime_rules_dir() == tmp_path / "src" / "rules"
