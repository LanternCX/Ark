from typer.testing import CliRunner
from pathlib import Path

import ark.cli as cli_module
from ark.cli import app
from ark.pipeline.config import PipelineConfig


def test_cli_help_contains_ark_description() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Ark backup agent" in result.stdout


def test_cli_root_invokes_main_menu_flow(monkeypatch) -> None:
    runner = CliRunner()
    invoked = False

    def fake_run_main_menu_flow() -> None:
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(cli_module, "run_main_menu_flow", fake_run_main_menu_flow)
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert invoked is True


def test_execute_backup_expands_user_paths(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run_backup_pipeline(**kwargs):
        observed.update(kwargs)
        return ["ok"]

    monkeypatch.setattr(cli_module, "run_backup_pipeline", fake_run_backup_pipeline)

    config = PipelineConfig(
        target="~/backup",
        source_roots=["~/Code"],
        dry_run=True,
    )

    cli_module._execute_backup(config)

    expected_root = (Path.home() / "Code").resolve()
    expected_target = str((Path.home() / "backup").resolve())
    assert observed["source_roots"] == [expected_root]
    assert observed["target"] == expected_target
