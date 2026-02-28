"""JSON-backed persistent config store."""

import json
from pathlib import Path

from ark.pipeline.config import PipelineConfig
from ark.state.base import ensure_parent_exists


class JSONConfigStore:
    """Persist and load pipeline configuration from a JSON file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        ensure_parent_exists(file_path)

    def load(self) -> PipelineConfig:
        """Load config from disk, returning defaults when absent."""
        if not self.file_path.exists():
            return PipelineConfig()

        payload = json.loads(self.file_path.read_text(encoding="utf-8"))
        return PipelineConfig(
            target=str(payload.get("target", "")),
            source_roots=list(payload.get("source_roots", [])),
            dry_run=bool(payload.get("dry_run", False)),
            non_interactive=bool(payload.get("non_interactive", False)),
        )

    def save(self, config: PipelineConfig) -> None:
        """Save config to disk."""
        payload = {
            "target": config.target,
            "source_roots": config.source_roots,
            "dry_run": config.dry_run,
            "non_interactive": config.non_interactive,
        }
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
