"""CLI entrypoint for Ark."""

from pathlib import Path

import typer

from ark.pipeline.run_backup import run_backup_pipeline
from ark.tui.stage1_review import SuffixReviewRow
from ark.tui.stage3_review import PathReviewRow

app = typer.Typer(help="Ark backup agent")
backup_app = typer.Typer(help="Backup commands")
app.add_typer(backup_app, name="backup")


@backup_app.command("run")
def run_backup(
    target: str = typer.Option(..., "--target", help="Backup target path"),
    source: list[str] = typer.Option(
        [], "--source", help="Source root path, repeat for multiple roots"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without file copy"),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Use default safe decisions without TUI prompts",
    ),
) -> None:
    """Run backup pipeline."""
    stage1_review_fn = _non_interactive_stage1 if non_interactive else None
    stage3_review_fn = _non_interactive_stage3 if non_interactive else None
    source_roots = [Path(item).resolve() for item in source] if source else None

    for line in run_backup_pipeline(
        target=target,
        dry_run=dry_run,
        source_roots=source_roots,
        stage1_review_fn=stage1_review_fn,
        stage3_review_fn=stage3_review_fn,
    ):
        typer.echo(line)


def _non_interactive_stage1(rows: list[SuffixReviewRow]) -> set[str]:
    """Select conservative defaults for stage 1 when prompts are disabled."""
    return {row.ext for row in rows if row.label == "keep" and row.confidence >= 0.8}


def _non_interactive_stage3(rows: list[PathReviewRow]) -> set[str]:
    """Select Tier 1 only when prompts are disabled."""
    return {row.path for row in rows if row.tier == "tier1"}


def main() -> None:
    """Run CLI app."""
    app()


if __name__ == "__main__":
    main()
