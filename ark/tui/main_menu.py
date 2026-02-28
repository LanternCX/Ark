"""Top-level TUI menu for Ark runtime configuration and execution."""

from collections.abc import Callable

import questionary
import typer

from ark.ai.google_oauth import run_browser_oauth_login
from ark.ai.router import check_llm_connectivity
from ark.pipeline.config import PipelineConfig
from ark.tui.llm_catalog import (
    LLM_PROVIDER_GROUPS,
    LLMProviderPreset,
    find_provider_group,
)


def run_main_menu(
    config: PipelineConfig,
    save_config: Callable[[PipelineConfig], None],
    execute_backup: Callable[[PipelineConfig], list[str]],
    select_prompt: Callable[[str, list[str]], str] | None = None,
    text_prompt: Callable[[str, str], str] | None = None,
    confirm_prompt: Callable[[str, bool], bool] | None = None,
    password_prompt: Callable[[str, str], str] | None = None,
    oauth_login: Callable[[str, str], str] | None = None,
    llm_connectivity_check: Callable[[PipelineConfig], tuple[bool, str]] | None = None,
    echo: Callable[[str], None] | None = None,
) -> None:
    """Run main menu loop until user exits."""
    select_fn = select_prompt or _default_select_prompt
    text_fn = text_prompt or _default_text_prompt
    confirm_fn = confirm_prompt or _default_confirm_prompt
    password_fn = password_prompt or _default_password_prompt
    oauth_login_fn = oauth_login or run_browser_oauth_login
    llm_connectivity_fn = llm_connectivity_check or _default_llm_connectivity_check
    echo_fn = echo or typer.echo

    while True:
        action = select_fn("Ark Main Menu", ["Settings", "Execute Backup", "Exit"])
        if action == "Settings":
            _run_settings(
                config,
                save_config,
                select_fn,
                text_fn,
                confirm_fn,
                password_fn,
                oauth_login_fn,
                llm_connectivity_fn,
                echo_fn,
            )
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
    select_prompt: Callable[[str, list[str]], str],
    text_prompt: Callable[[str, str], str],
    confirm_prompt: Callable[[str, bool], bool],
    password_prompt: Callable[[str, str], str],
    oauth_login: Callable[[str, str], str],
    llm_connectivity_check: Callable[[PipelineConfig], tuple[bool, str]],
    echo: Callable[[str], None],
) -> None:
    while True:
        section = select_prompt(
            "Settings",
            ["Backup Settings", "LLM Settings", "Back"],
        )
        if section == "Backup Settings":
            _run_backup_settings(config, save_config, text_prompt, confirm_prompt)
            continue
        if section == "LLM Settings":
            _run_llm_settings(
                config,
                save_config,
                select_prompt,
                text_prompt,
                confirm_prompt,
                password_prompt,
                oauth_login,
                llm_connectivity_check,
                echo,
            )
            continue
        return


def _run_backup_settings(
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

    config.target = target.strip()
    config.source_roots = [
        item.strip() for item in source_input.split(",") if item.strip()
    ]
    config.dry_run = dry_run
    config.non_interactive = non_interactive
    save_config(config)


def _run_llm_settings(
    config: PipelineConfig,
    save_config: Callable[[PipelineConfig], None],
    select_prompt: Callable[[str, list[str]], str],
    text_prompt: Callable[[str, str], str],
    confirm_prompt: Callable[[str, bool], bool],
    password_prompt: Callable[[str, str], str],
    oauth_login: Callable[[str, str], str],
    llm_connectivity_check: Callable[[PipelineConfig], tuple[bool, str]],
    echo: Callable[[str], None],
) -> None:
    enabled = confirm_prompt("Enable LiteLLM integration?", config.llm_enabled)
    config.llm_enabled = enabled
    if not enabled:
        save_config(config)
        return

    group_choices = _with_default_first(
        list(LLM_PROVIDER_GROUPS.keys()),
        config.llm_provider_group or find_provider_group(config.llm_provider),
    )
    selected_group = select_prompt("LLM provider group", group_choices)
    provider_presets = LLM_PROVIDER_GROUPS.get(
        selected_group, LLM_PROVIDER_GROUPS[group_choices[0]]
    )

    provider_labels = [_provider_label(preset) for preset in provider_presets]
    default_label = ""
    for preset in provider_presets:
        if preset.provider == config.llm_provider:
            default_label = _provider_label(preset)
            break
    provider_labels = _with_default_first(provider_labels, default_label)

    selected_provider_label = select_prompt("LLM platform", provider_labels)
    selected_preset = _preset_from_label(provider_presets, selected_provider_label)

    recommended_model_choices = _with_default_first(
        list(selected_preset.models),
        config.llm_model
        if config.llm_model in selected_preset.models
        else selected_preset.default_model,
    )
    selected_model_preset = select_prompt(
        "Recommended model preset",
        recommended_model_choices,
    )

    has_existing_custom_model = (
        config.llm_provider == selected_preset.provider
        and config.llm_model
        and config.llm_model not in selected_preset.models
    )
    override_model = confirm_prompt(
        "Override recommended model?", has_existing_custom_model
    )
    if override_model:
        text_default_model = (
            config.llm_model
            if config.llm_provider == selected_preset.provider and config.llm_model
            else selected_model_preset
        )
        model = (
            text_prompt("LLM model (custom allowed)", text_default_model).strip()
            or text_default_model
        )
    else:
        model = selected_model_preset

    default_base_url = (
        config.llm_base_url
        if config.llm_provider == selected_preset.provider and config.llm_base_url
        else selected_preset.base_url
    )
    base_url = ""
    if selected_preset.allow_base_url or selected_preset.base_url:
        base_url = (
            text_prompt("LLM base URL (optional)", default_base_url).strip()
            or default_base_url
        )

    auth_method = "api_key"
    if selected_preset.provider == "gemini":
        auth_method = select_prompt(
            "Gemini authentication method",
            _with_default_first(
                ["api_key", "google_oauth"],
                config.llm_auth_method,
            ),
        )

    api_key = ""
    google_client_id = ""
    google_client_secret = ""
    google_refresh_token = ""

    if auth_method == "google_oauth" and selected_preset.provider == "gemini":
        google_client_id = text_prompt(
            "Google client id", config.google_client_id
        ).strip()
        google_client_secret = password_prompt(
            "Google client secret",
            config.google_client_secret,
        ).strip()
        google_refresh_token = config.google_refresh_token.strip()
        should_login = confirm_prompt(
            "Login with Google in browser now?",
            not bool(google_refresh_token),
        )
        if should_login:
            google_refresh_token = oauth_login(
                google_client_id,
                google_client_secret,
            ).strip()
    elif selected_preset.requires_api_key:
        default_api_key = (
            config.llm_api_key
            if config.llm_provider == selected_preset.provider and config.llm_api_key
            else ""
        )
        api_key = password_prompt("LLM API key", default_api_key).strip()

    ai_suffix_enabled = confirm_prompt(
        "Use AI suffix risk classification?", config.ai_suffix_enabled
    )
    ai_path_enabled = confirm_prompt(
        "Use AI path pruning suggestions?", config.ai_path_enabled
    )
    send_full_path_to_ai = confirm_prompt(
        "Send full file paths to AI?", config.send_full_path_to_ai
    )
    hide_low_value_default = confirm_prompt(
        "Hide low-value branches by default?",
        config.ai_prune_mode == "hide_low_value",
    )

    config.llm_enabled = True
    config.llm_provider_group = selected_group
    config.llm_provider = selected_preset.provider
    config.llm_model = model
    config.llm_base_url = base_url
    config.llm_api_key = api_key
    config.llm_auth_method = auth_method
    config.google_client_id = google_client_id
    config.google_client_secret = google_client_secret
    config.google_refresh_token = google_refresh_token
    config.ai_suffix_enabled = ai_suffix_enabled
    config.ai_path_enabled = ai_path_enabled
    config.send_full_path_to_ai = send_full_path_to_ai
    config.ai_prune_mode = "hide_low_value" if hide_low_value_default else "show_all"

    should_test_connectivity = confirm_prompt("Test LLM connectivity now?", True)
    if should_test_connectivity:
        ok, message = llm_connectivity_check(config)
        if ok:
            echo(f"LLM connectivity test passed: {message}")
        else:
            echo(f"LLM connectivity test failed: {message}")

    save_config(config)


def _provider_label(preset: LLMProviderPreset) -> str:
    return preset.name


def _preset_from_label(
    presets: list[LLMProviderPreset],
    label: str,
) -> LLMProviderPreset:
    for preset in presets:
        if _provider_label(preset) == label:
            return preset
    return presets[0]


def _with_default_first(choices: list[str], default_choice: str | None) -> list[str]:
    if not default_choice or default_choice not in choices:
        return choices
    return [default_choice] + [choice for choice in choices if choice != default_choice]


def _default_select_prompt(message: str, choices: list[str]) -> str:
    result = questionary.select(message=message, choices=choices).ask()
    return result or "Exit"


def _default_text_prompt(message: str, default: str) -> str:
    result = questionary.text(message=message, default=default).ask()
    return result or default


def _default_confirm_prompt(message: str, default: bool) -> bool:
    result = questionary.confirm(message=message, default=default).ask()
    return bool(result)


def _default_password_prompt(message: str, default: str) -> str:
    result = questionary.password(message=message, default=default).ask()
    return result or default


def _default_llm_connectivity_check(config: PipelineConfig) -> tuple[bool, str]:
    return check_llm_connectivity(
        model=config.llm_model,
        provider=config.llm_provider,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        auth_method=config.llm_auth_method,
        google_client_id=config.google_client_id,
        google_client_secret=config.google_client_secret,
        google_refresh_token=config.google_refresh_token,
    )
