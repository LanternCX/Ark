from typer.testing import CliRunner

import ark.cli as cli_module
from ark.cli import app


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
