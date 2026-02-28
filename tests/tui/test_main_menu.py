from ark.pipeline.config import PipelineConfig
from ark.tui.main_menu import run_main_menu


def test_main_menu_settings_then_execute_then_exit() -> None:
    config = PipelineConfig()
    saved: list[PipelineConfig] = []
    observed_execute: list[PipelineConfig] = []
    output: list[str] = []

    main_choices = iter(["Settings", "Execute Backup", "Exit"])
    text_values = iter(["X:/ArkBackup", ".,./docs"])
    confirm_values = iter([True, True])

    def select_prompt(message: str, choices: list[str]) -> str:
        del message, choices
        return next(main_choices)

    def text_prompt(message: str, default: str) -> str:
        del message, default
        return next(text_values)

    def confirm_prompt(message: str, default: bool) -> bool:
        del message, default
        return next(confirm_values)

    def save_config(updated: PipelineConfig) -> None:
        saved.append(updated)

    def execute_backup(current: PipelineConfig) -> list[str]:
        observed_execute.append(current)
        return ["Stage 1", "Stage 2", "Stage 3"]

    def echo(line: str) -> None:
        output.append(line)

    run_main_menu(
        config=config,
        save_config=save_config,
        execute_backup=execute_backup,
        select_prompt=select_prompt,
        text_prompt=text_prompt,
        confirm_prompt=confirm_prompt,
        echo=echo,
    )

    assert len(saved) == 1
    assert saved[0].target == "X:/ArkBackup"
    assert saved[0].source_roots == [".", "./docs"]
    assert saved[0].dry_run is True
    assert saved[0].non_interactive is True

    assert len(observed_execute) == 1
    assert observed_execute[0].target == "X:/ArkBackup"
    assert "Stage 1" in output


def test_main_menu_shows_validation_errors_when_required_fields_missing() -> None:
    config = PipelineConfig()
    output: list[str] = []
    main_choices = iter(["Execute Backup", "Exit"])

    def select_prompt(message: str, choices: list[str]) -> str:
        del message, choices
        return next(main_choices)

    run_main_menu(
        config=config,
        save_config=lambda _: None,
        execute_backup=lambda _: ["should not run"],
        select_prompt=select_prompt,
        text_prompt=lambda _message, default: default,
        confirm_prompt=lambda _message, default: default,
        echo=output.append,
    )

    assert any("target" in line.lower() for line in output)
    assert any("source" in line.lower() for line in output)
