from src.pipeline.config import PipelineConfig
from src.state.config_store import JSONConfigStore
from src.state.sqlite_store import SQLiteStateStore


def test_sqlite_store_can_create_and_load_session(tmp_path) -> None:
    db = tmp_path / "state.db"
    store = SQLiteStateStore(db)
    session_id = store.create_session("windows")
    loaded = store.get_session(session_id)
    assert loaded.platform == "windows"


def test_config_store_roundtrip(tmp_path) -> None:
    store = JSONConfigStore(tmp_path / "config.json")
    config = PipelineConfig(
        target="X:/ArkBackup",
        source_roots=["C:/Users/me/Documents", "C:/Users/me/Pictures"],
        dry_run=True,
        non_interactive=False,
        llm_enabled=True,
        llm_provider_group="OpenAI & Compatible",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        llm_base_url="",
        llm_api_key="sk-test-key",
        llm_auth_method="api_key",
        google_client_id="client-id",
        google_client_secret="client-secret",
        google_refresh_token="refresh-token",
        ai_suffix_enabled=True,
        ai_path_enabled=True,
        send_full_path_to_ai=True,
        ai_prune_mode="hide_low_value",
    )

    store.save(config)
    loaded = store.load()

    assert loaded == config


def test_config_store_returns_default_when_file_missing(tmp_path) -> None:
    store = JSONConfigStore(tmp_path / "config.json")
    loaded = store.load()

    assert loaded.target == ""
    assert loaded.source_roots == []
    assert loaded.dry_run is False
    assert loaded.non_interactive is False
    assert loaded.llm_enabled is False
    assert loaded.llm_provider_group == ""
    assert loaded.llm_provider == ""
    assert loaded.llm_model == ""
    assert loaded.llm_base_url == ""
    assert loaded.llm_api_key == ""
    assert loaded.llm_auth_method == "api_key"
    assert loaded.google_client_id == ""
    assert loaded.google_client_secret == ""
    assert loaded.google_refresh_token == ""
    assert loaded.ai_suffix_enabled is True
    assert loaded.ai_path_enabled is True
    assert loaded.send_full_path_to_ai is False
    assert loaded.ai_prune_mode == "hide_low_value"
