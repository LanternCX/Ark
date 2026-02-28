from typer.testing import CliRunner

from ark.cli import app


def test_backup_run_command_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "backup",
            "run",
            "--target",
            "X:/ArkBackup",
            "--dry-run",
            "--non-interactive",
        ],
    )
    assert result.exit_code == 0
    assert "Stage 1" in result.stdout
    assert "Stage 2" in result.stdout
    assert "Stage 3" in result.stdout
