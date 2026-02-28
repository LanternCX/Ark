"""Pipeline runtime configuration contracts."""

from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    """User-editable runtime configuration for backup pipeline execution."""

    target: str = ""
    source_roots: list[str] = field(default_factory=list)
    dry_run: bool = False
    non_interactive: bool = False
    llm_enabled: bool = False
    llm_provider_group: str = ""
    llm_provider: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_auth_method: str = "api_key"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    ai_suffix_enabled: bool = True
    ai_path_enabled: bool = True
    send_full_path_to_ai: bool = False
    ai_prune_mode: str = "hide_low_value"

    def validate_for_execution(self) -> list[str]:
        """Return a list of validation errors blocking pipeline execution."""
        errors: list[str] = []
        if not self.target.strip():
            errors.append("target is required")
        if not self.source_roots:
            errors.append("source roots are required")
        if self.llm_enabled and not self.llm_provider.strip():
            errors.append("llm provider is required when litellm is enabled")
        if self.llm_enabled and not self.llm_model.strip():
            errors.append("llm model is required when litellm is enabled")
        if self.llm_enabled and self.llm_provider == "gemini":
            if self.llm_auth_method not in {"api_key", "google_oauth"}:
                errors.append("gemini auth method must be api_key or google_oauth")
            if self.llm_auth_method == "google_oauth":
                if not self.google_client_id.strip():
                    errors.append("google client id is required for gemini oauth")
                if not self.google_client_secret.strip():
                    errors.append("google client secret is required for gemini oauth")
                if not self.google_refresh_token.strip():
                    errors.append("google refresh token is required for gemini oauth")
        if self.ai_prune_mode not in {"hide_low_value", "show_all"}:
            errors.append("ai prune mode must be hide_low_value or show_all")
        return errors
