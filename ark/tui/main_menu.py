"""Top-level TUI menu for Ark runtime configuration and execution."""

from collections.abc import Callable

import questionary
import typer

from ark.pipeline.config import PipelineConfig


def run_main_menu(
    config: PipelineConfig,
    save_config: Callable[[PipelineConfig], None],
    execute_backup: Callable[[PipelineConfig], list[str]],
    select_prompt: Callable[[str, list[str]], str] | None = None,
    text_prompt: Callable[[str, str], str] | None = None,
    confirm_prompt: Callable[[str, bool], bool] | None = None,
    echo: Callable[[str], None] | None = None,
) -> None:
    """Run main menu loop until user exits."""
    select_fn = select_prompt or _default_select_prompt
    text_fn = text_prompt or _default_text_prompt
    confirm_fn = confirm_prompt or _default_confirm_prompt
    echo_fn = echo or typer.echo

    while True:
        action = select_fn("Ark Main Menu", ["Settings", "Execute Backup", "Exit"])
        if action == "Settings":
            _run_settings(config, save_config, text_fn, confirm_fn)
            echo_fn("Settings saved.")
            continue

        if action == "Execute Backup":
            errors = config.validate_for_execution()
            if errors:
                for error in errors:
                    echo_fn(f"Configuration error: {error}")
                continue

            for line in execute_backup(config):
                echo_fn(line)
            continue

        return


def _run_settings(
    config: PipelineConfig,
    save_config: Callable[[PipelineConfig], None],
    text_prompt: Callable[[str, str], str],
    confirm_prompt: Callable[[str, bool], bool],
) -> None:
    target = text_prompt("Backup target path", config.target)
    source_input = text_prompt(
        "Source roots (comma separated)", ",".join(config.source_roots)
    )
    dry_run = confirm_prompt("Dry run?", config.dry_run)
    non_interactive = confirm_prompt("Non-interactive reviews?", config.non_interactive)

    normalized_roots = [
        item.strip() for item in source_input.split(",") if item.strip()
    ]
    config.target = target.strip()
    config.source_roots = normalized_roots
    config.dry_run = dry_run
    config.non_interactive = non_interactive
    save_config(config)


def _default_select_prompt(message: str, choices: list[str]) -> str:
    result = questionary.select(message=message, choices=choices).ask()
    return result or "Exit"


def _default_text_prompt(message: str, default: str) -> str:
    result = questionary.text(message=message, default=default).ask()
    return result or default


def _default_confirm_prompt(message: str, default: bool) -> bool:
    result = questionary.confirm(message=message, default=default).ask()
    return bool(result)
