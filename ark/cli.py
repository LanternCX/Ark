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
        suffix_risk_fn=_heuristic_suffix_risk if config.ai_suffix_enabled else None,
        path_risk_fn=_heuristic_path_risk if config.ai_path_enabled else None,
        send_full_path_to_ai=config.send_full_path_to_ai,
        ai_prune_mode=config.ai_prune_mode,
    )


def _non_interactive_stage1(rows: list[SuffixReviewRow]) -> set[str]:
    """Select conservative defaults for stage 1 when prompts are disabled."""
    return {row.ext for row in rows if row.label == "keep" and row.confidence >= 0.8}


def _non_interactive_stage3(rows: list[PathReviewRow]) -> set[str]:
    """Select Tier 1 only when prompts are disabled."""
    return {row.path for row in rows if row.tier == "tier1"}


def _heuristic_suffix_risk(exts: list[str]) -> dict[str, dict[str, object]]:
    """Return local heuristic suffix risk map when AI suggestion is enabled."""
    high_value = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".txt", ".md"}
    low_value = {".tmp", ".cache", ".log"}
    result: dict[str, dict[str, object]] = {}
    for ext in exts:
        if ext in high_value:
            result[ext] = {
                "risk": "high_value",
                "confidence": 0.85,
                "reason": "Likely user-authored or irreplaceable data",
            }
        elif ext in low_value:
            result[ext] = {
                "risk": "low_value",
                "confidence": 0.85,
                "reason": "Likely disposable generated artifact",
            }
        else:
            result[ext] = {
                "risk": "neutral",
                "confidence": 0.5,
                "reason": "No strong suffix signal",
            }
    return result


def _heuristic_path_risk(paths: list[str]) -> dict[str, dict[str, object]]:
    """Return local heuristic path risk map when AI suggestion is enabled."""
    result: dict[str, dict[str, object]] = {}
    for path in paths:
        lower = path.lower()
        if any(token in lower for token in ["tmp", "cache", "node_modules", ".git"]):
            result[path] = {
                "risk": "low_value",
                "confidence": 0.9,
                "score": 0.2,
                "reason": "Path pattern suggests low-value or reproducible artifact",
            }
        elif any(
            token in lower for token in ["documents", "desktop", "pictures", "photo"]
        ):
            result[path] = {
                "risk": "high_value",
                "confidence": 0.9,
                "score": 0.85,
                "reason": "Path pattern suggests personal or work-critical content",
            }
        else:
            result[path] = {
                "risk": "neutral",
                "confidence": 0.55,
                "score": 0.5,
                "reason": "No strong path-level preference",
            }
    return result


def main() -> None:
    """Run CLI app."""
    app()


if __name__ == "__main__":
    main()
