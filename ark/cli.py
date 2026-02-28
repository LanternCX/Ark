"""CLI entrypoint for Ark."""

from pathlib import Path

import typer

from ark.pipeline.config import PipelineConfig
from ark.pipeline.run_backup import run_backup_pipeline
from ark.state.config_store import JSONConfigStore
from ark.tui.main_menu import run_main_menu
from ark.tui.stage1_review import SuffixReviewRow
from ark.tui.stage3_review import PathReviewRow

app = typer.Typer(help="Ark backup agent")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Run Ark top-level TUI flow."""
    if ctx.invoked_subcommand is None:
        run_main_menu_flow()


def run_main_menu_flow() -> None:
    """Load persisted config and start interactive main menu."""
    store = JSONConfigStore(Path.home() / ".ark" / "config.json")
    config = store.load()

    run_main_menu(
        config=config,
        save_config=store.save,
        execute_backup=_execute_backup,
    )


def _execute_backup(config: PipelineConfig) -> list[str]:
    stage1_review_fn = _non_interactive_stage1 if config.non_interactive else None
    stage3_review_fn = _non_interactive_stage3 if config.non_interactive else None
    source_roots = [Path(item).expanduser().resolve() for item in config.source_roots]
    target = str(Path(config.target).expanduser().resolve())

    return run_backup_pipeline(
        target=target,
        dry_run=config.dry_run,
        source_roots=source_roots,
        stage1_review_fn=stage1_review_fn,
        stage3_review_fn=stage3_review_fn,
    )


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
