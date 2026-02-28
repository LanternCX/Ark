from ark.pipeline.config import PipelineConfig
from ark.state.config_store import JSONConfigStore
from ark.state.sqlite_store import SQLiteStateStore


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
