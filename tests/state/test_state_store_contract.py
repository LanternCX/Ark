from ark.state.sqlite_store import SQLiteStateStore


def test_sqlite_store_can_create_and_load_session(tmp_path) -> None:
    db = tmp_path / "state.db"
    store = SQLiteStateStore(db)
    session_id = store.create_session("windows")
    loaded = store.get_session(session_id)
    assert loaded.platform == "windows"
