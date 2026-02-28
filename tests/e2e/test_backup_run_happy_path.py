from typer.testing import CliRunner

from ark.cli import app


def test_backup_run_command_smoke() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("note.txt", "w", encoding="utf-8") as handle:
            handle.write("hello")

        result = runner.invoke(
            app,
            [
                "backup",
                "run",
                "--target",
                "X:/ArkBackup",
                "--source",
                ".",
                "--dry-run",
                "--non-interactive",
            ],
        )
    assert result.exit_code == 0
    assert "Stage 1" in result.stdout
    assert "Stage 2" in result.stdout
    assert "Stage 3" in result.stdout
