from src.pipeline.config import PipelineConfig
from src.tui.main_menu import run_main_menu


def test_main_menu_settings_then_execute_then_exit() -> None:
    config = PipelineConfig()
    saved: list[PipelineConfig] = []
    observed_execute: list[PipelineConfig] = []
    output: list[str] = []

    main_choices = iter(["Settings", "Execute Backup", "Exit"])
    settings_choices = iter(["Backup Settings", "Back"])
    text_values = iter(["X:/ArkBackup", ".,./docs"])
    confirm_values = iter([True, True])

    def select_prompt(message: str, choices: list[str]) -> str:
        del choices
        if message == "Ark Main Menu":
            return next(main_choices)
        return next(settings_choices)

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
        password_prompt=lambda _message, default: default,
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
        password_prompt=lambda _message, default: default,
        echo=output.append,
    )

    assert any("target" in line.lower() for line in output)
    assert any("source" in line.lower() for line in output)


def test_main_menu_can_save_llm_settings() -> None:
    config = PipelineConfig()
    saved: list[PipelineConfig] = []

    main_choices = iter(["Settings", "Exit"])
    settings_choices = iter(["LLM Settings", "Back"])
    llm_choices = iter(
        [
            "OpenAI & Compatible",
            "OpenAI",
            "openai/gpt-4.1",
        ]
    )

    def select_prompt(message: str, choices: list[str]) -> str:
        del choices
        if message == "Ark Main Menu":
            return next(main_choices)
        if message == "Settings":
            return next(settings_choices)
        return next(llm_choices)

    def save_config(updated: PipelineConfig) -> None:
        saved.append(updated)

    run_main_menu(
        config=config,
        save_config=save_config,
        execute_backup=lambda _: [],
        select_prompt=select_prompt,
        text_prompt=lambda message, default: (
            "gpt-4.1-mini-custom"
            if message == "LLM model (custom allowed)"
            else default
        ),
        confirm_prompt=lambda _message, _default: True,
        password_prompt=lambda _message, _default: "sk-test-key",
        echo=lambda _line: None,
    )

    assert len(saved) == 1
    assert saved[0].llm_enabled is True
    assert saved[0].llm_provider_group == "OpenAI & Compatible"
    assert saved[0].llm_provider == "openai"
    assert saved[0].llm_model == "gpt-4.1-mini-custom"
    assert saved[0].llm_api_key == "sk-test-key"
    assert saved[0].ai_suffix_enabled is True
    assert saved[0].ai_path_enabled is True
    assert saved[0].send_full_path_to_ai is True
    assert saved[0].ai_prune_mode == "hide_low_value"


def test_main_menu_can_save_gemini_oauth_settings() -> None:
    config = PipelineConfig()
    saved: list[PipelineConfig] = []

    main_choices = iter(["Settings", "Exit"])
    settings_choices = iter(["LLM Settings", "Back"])
    llm_choices = iter(
        [
            "Frontier Models",
            "Google Gemini",
            "gemini/gemini-3-flash",
            "google_oauth",
        ]
    )

    def select_prompt(message: str, choices: list[str]) -> str:
        del choices
        if message == "Ark Main Menu":
            return next(main_choices)
        if message == "Settings":
            return next(settings_choices)
        return next(llm_choices)

    def save_config(updated: PipelineConfig) -> None:
        saved.append(updated)

    run_main_menu(
        config=config,
        save_config=save_config,
        execute_backup=lambda _: [],
        select_prompt=select_prompt,
        text_prompt=lambda message, default: (
            "gemini/gemini-3-pro-custom"
            if message == "LLM model (custom allowed)"
            else ("client-id-value" if message == "Google client id" else default)
        ),
        confirm_prompt=lambda _message, _default: True,
        password_prompt=lambda message, default: (
            "client-secret-value" if message == "Google client secret" else default
        ),
        oauth_login=lambda _client_id, _client_secret: "refresh-token-xyz",
        echo=lambda _line: None,
    )

    assert len(saved) == 1
    assert saved[0].llm_enabled is True
    assert saved[0].llm_provider == "gemini"
    assert saved[0].llm_auth_method == "google_oauth"
    assert saved[0].llm_model == "gemini/gemini-3-pro-custom"
    assert saved[0].google_client_id == "client-id-value"
    assert saved[0].google_client_secret == "client-secret-value"
    assert saved[0].google_refresh_token == "refresh-token-xyz"


def test_main_menu_can_run_llm_connectivity_check() -> None:
    config = PipelineConfig()
    output: list[str] = []

    main_choices = iter(["Settings", "Exit"])
    settings_choices = iter(["LLM Settings", "Back"])
    llm_choices = iter(
        [
            "China-Friendly",
            "GLM (Zhipu)",
            "zai/glm-4.5",
        ]
    )

    def select_prompt(message: str, choices: list[str]) -> str:
        del choices
        if message == "Ark Main Menu":
            return next(main_choices)
        if message == "Settings":
            return next(settings_choices)
        return next(llm_choices)

    def fake_connectivity_check(current: PipelineConfig) -> tuple[bool, str]:
        assert current.llm_provider == "zhipuai"
        assert current.llm_model == "zai/glm-4.5"
        return True, "ok"

    run_main_menu(
        config=config,
        save_config=lambda _: None,
        execute_backup=lambda _: [],
        select_prompt=select_prompt,
        text_prompt=lambda _message, default: default,
        confirm_prompt=lambda message, default: (
            True
            if message in {"Enable LiteLLM integration?", "Test LLM connectivity now?"}
            else default
        ),
        password_prompt=lambda _message, _default: "sk-test-key",
        llm_connectivity_check=fake_connectivity_check,
        echo=output.append,
    )

    assert any("LLM connectivity test passed" in line for line in output)
    assert any("ok" in line for line in output)


def test_main_menu_can_accept_recommended_model_without_custom_override() -> None:
    config = PipelineConfig()
    saved: list[PipelineConfig] = []

    main_choices = iter(["Settings", "Exit"])
    settings_choices = iter(["LLM Settings", "Back"])
    llm_choices = iter(
        [
            "China-Friendly",
            "GLM (Zhipu)",
            "zai/glm-4.7",
        ]
    )

    def select_prompt(message: str, choices: list[str]) -> str:
        del choices
        if message == "Ark Main Menu":
            return next(main_choices)
        if message == "Settings":
            return next(settings_choices)
        return next(llm_choices)

    def text_prompt(message: str, default: str) -> str:
        if message == "LLM model (custom allowed)":
            raise AssertionError("custom model prompt should not be shown")
        return default

    def confirm_prompt(message: str, default: bool) -> bool:
        if message == "Enable LiteLLM integration?":
            return True
        if message == "Override recommended model?":
            return False
        if message == "Test LLM connectivity now?":
            return False
        return default

    run_main_menu(
        config=config,
        save_config=saved.append,
        execute_backup=lambda _: [],
        select_prompt=select_prompt,
        text_prompt=text_prompt,
        confirm_prompt=confirm_prompt,
        password_prompt=lambda _message, _default: "sk-test-key",
        echo=lambda _line: None,
    )

    assert len(saved) == 1
    assert saved[0].llm_provider == "zhipuai"
    assert saved[0].llm_model == "zai/glm-4.7"
