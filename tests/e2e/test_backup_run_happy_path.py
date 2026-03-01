from typer.testing import CliRunner
import typer

import src.cli as cli_module
from src.cli import app


def test_ark_root_command_smoke(monkeypatch) -> None:
    runner = CliRunner()

    def fake_run_main_menu_flow() -> None:
        typer.echo("Stage 1: Suffix Screening")
        typer.echo("Stage 2: Path Tiering")
        typer.echo("Stage 3: Final Review and Backup")

    monkeypatch.setattr(cli_module, "run_main_menu_flow", fake_run_main_menu_flow)
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Stage 1" in result.stdout
    assert "Stage 2" in result.stdout
    assert "Stage 3" in result.stdout
