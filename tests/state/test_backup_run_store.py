from pathlib import Path

from src.state.backup_run_store import BackupRunStore


def test_backup_run_store_can_create_checkpoint_and_resume_latest(
    tmp_path: Path,
) -> None:
    store = BackupRunStore(tmp_path)
    run_id = store.create_run(
        target="/backup",
        source_roots=["/data/a", "/data/b"],
        dry_run=True,
    )

    store.save_checkpoint(
        run_id,
        stage="scan",
        payload={"discovered_files": ["/data/a/1.txt"], "scan_complete": False},
    )
    store.mark_status(run_id, "paused")

    latest = store.find_latest_resumable(
        target="/backup",
        source_roots=["/data/a", "/data/b"],
        dry_run=True,
    )

    assert latest is not None
    assert latest["run_id"] == run_id
    assert latest["status"] == "paused"
    assert latest["state"]["checkpoints"]["scan"]["discovered_files"] == [
        "/data/a/1.txt"
    ]


def test_backup_run_store_increments_checkpoint_sequence(tmp_path: Path) -> None:
    store = BackupRunStore(tmp_path)
    run_id = store.create_run(
        target="/backup",
        source_roots=["/data"],
        dry_run=False,
    )

    store.save_checkpoint(run_id, stage="scan", payload={"count": 1})
    store.save_checkpoint(run_id, stage="scan", payload={"count": 2})

    state = store.load_run(run_id)
    assert state["meta"]["checkpoint_seq"] == 2
    assert state["meta"]["last_stage"] == "scan"
    assert state["checkpoints"]["scan"]["count"] == 2


def test_backup_run_store_writes_structured_events(tmp_path: Path) -> None:
    store = BackupRunStore(tmp_path)
    run_id = store.create_run(
        target="/backup",
        source_roots=["/data"],
        dry_run=True,
    )

    store.append_event(
        run_id,
        stage="scan",
        event="scan.progress",
        payload={"files": 20},
    )

    content = (tmp_path / f"{run_id}.events.jsonl").read_text(encoding="utf-8")
    assert "scan.progress" in content
    assert '"files": 20' in content
