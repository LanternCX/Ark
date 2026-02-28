"""CLI entrypoint for Ark."""

import typer

app = typer.Typer(help="Ark backup agent")
backup_app = typer.Typer(help="Backup commands")
app.add_typer(backup_app, name="backup")


@backup_app.command("run")
def run_backup(
    target: str = typer.Option(..., "--target", help="Backup target path"),
) -> None:
    """Run backup pipeline."""
    typer.echo(f"Backup target: {target}")


def main() -> None:
    """Run CLI app."""
    app()


if __name__ == "__main__":
    main()
