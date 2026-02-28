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
            llm_enabled=bool(payload.get("llm_enabled", False)),
            llm_provider_group=str(payload.get("llm_provider_group", "")),
            llm_provider=str(payload.get("llm_provider", "")),
            llm_model=str(payload.get("llm_model", "")),
            llm_base_url=str(payload.get("llm_base_url", "")),
            llm_api_key=str(payload.get("llm_api_key", "")),
            llm_auth_method=str(payload.get("llm_auth_method", "api_key")),
            google_client_id=str(payload.get("google_client_id", "")),
            google_client_secret=str(payload.get("google_client_secret", "")),
            google_refresh_token=str(payload.get("google_refresh_token", "")),
        )

    def save(self, config: PipelineConfig) -> None:
        """Save config to disk."""
        payload = {
            "target": config.target,
            "source_roots": config.source_roots,
            "dry_run": config.dry_run,
            "non_interactive": config.non_interactive,
            "llm_enabled": config.llm_enabled,
            "llm_provider_group": config.llm_provider_group,
            "llm_provider": config.llm_provider,
            "llm_model": config.llm_model,
            "llm_base_url": config.llm_base_url,
            "llm_api_key": config.llm_api_key,
            "llm_auth_method": config.llm_auth_method,
            "google_client_id": config.google_client_id,
            "google_client_secret": config.google_client_secret,
            "google_refresh_token": config.google_refresh_token,
        }
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
