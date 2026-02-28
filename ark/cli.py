"""CLI entrypoint for Ark."""

import typer

from ark.pipeline.run_backup import run_backup_pipeline

app = typer.Typer(help="Ark backup agent")
backup_app = typer.Typer(help="Backup commands")
app.add_typer(backup_app, name="backup")


@backup_app.command("run")
def run_backup(
    target: str = typer.Option(..., "--target", help="Backup target path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without file copy"),
) -> None:
    """Run backup pipeline."""
    for line in run_backup_pipeline(target=target, dry_run=dry_run):
        typer.echo(line)


def main() -> None:
    """Run CLI app."""
    app()


if __name__ == "__main__":
    main()
