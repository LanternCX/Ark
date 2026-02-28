from typer.testing import CliRunner

from ark.cli import app


def test_cli_help_contains_backup_group() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "backup" in result.stdout
