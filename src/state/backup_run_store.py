"""Run checkpoint persistence for resumable backup execution."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BackupRunStore:
    """Persist backup run metadata and checkpoints under one directory."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, target: str, source_roots: list[str], dry_run: bool) -> str:
        """Create a new run state file and return run id."""
        run_id = str(uuid.uuid4())
        state = {
            "run_id": run_id,
            "meta": {
                "status": "running",
                "target": target,
                "source_roots": sorted(source_roots),
                "dry_run": bool(dry_run),
                "started_at": _utc_now(),
                "updated_at": _utc_now(),
                "checkpoint_seq": 0,
                "last_stage": "",
            },
            "checkpoints": {},
        }
        self._write_run_state(run_id, state)
        return run_id

    def load_run(self, run_id: str) -> dict:
        """Load one run state by id."""
        path = self._state_path(run_id)
        if not path.exists():
            raise KeyError(f"Run not found: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_checkpoint(self, run_id: str, stage: str, payload: dict) -> None:
        """Persist one stage checkpoint and increment checkpoint sequence."""
        state = self.load_run(run_id)
        seq = int(state["meta"].get("checkpoint_seq", 0)) + 1
        state["meta"]["checkpoint_seq"] = seq
        state["meta"]["last_stage"] = stage
        state["meta"]["updated_at"] = _utc_now()
        state["checkpoints"][stage] = payload
        self._write_run_state(run_id, state)

    def append_event(self, run_id: str, stage: str, event: str, payload: dict) -> None:
        """Append one structured event to per-run JSONL log."""
        record = {
            "ts": _utc_now(),
            "run_id": run_id,
            "stage": stage,
            "event": event,
            "payload": payload,
        }
        event_path = self._events_path(run_id)
        event_path.parent.mkdir(parents=True, exist_ok=True)
        with event_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    def mark_status(self, run_id: str, status: str) -> None:
        """Update run lifecycle status."""
        if status not in {"running", "paused", "failed", "completed", "discarded"}:
            raise ValueError("invalid run status")
        state = self.load_run(run_id)
        state["meta"]["status"] = status
        state["meta"]["updated_at"] = _utc_now()
        self._write_run_state(run_id, state)

    def find_latest_resumable(
        self,
        target: str,
        source_roots: list[str],
        dry_run: bool,
    ) -> dict | None:
        """Return latest paused/running matching run summary with state."""
        desired_roots = sorted(source_roots)
        candidates: list[dict] = []
        for path in sorted(self.root_dir.glob("*.json")):
            state = json.loads(path.read_text(encoding="utf-8"))
            meta = state.get("meta", {})
            if meta.get("status") not in {"paused", "running"}:
                continue
            if meta.get("target") != target:
                continue
            if sorted(meta.get("source_roots", [])) != desired_roots:
                continue
            if bool(meta.get("dry_run", False)) != bool(dry_run):
                continue
            candidates.append(state)

        if not candidates:
            return None

        latest = max(
            candidates, key=lambda item: item.get("meta", {}).get("updated_at", "")
        )
        return {
            "run_id": latest["run_id"],
            "status": latest["meta"]["status"],
            "state": latest,
        }

    def _state_path(self, run_id: str) -> Path:
        return self.root_dir / f"{run_id}.json"

    def _events_path(self, run_id: str) -> Path:
        return self.root_dir / f"{run_id}.events.jsonl"

    def _write_run_state(self, run_id: str, state: dict) -> None:
        path = self._state_path(run_id)
        temp = path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temp.replace(path)
