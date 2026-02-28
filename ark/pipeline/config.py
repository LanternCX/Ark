"""Pipeline runtime configuration contracts."""

from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    """User-editable runtime configuration for backup pipeline execution."""

    target: str = ""
    source_roots: list[str] = field(default_factory=list)
    dry_run: bool = False
    non_interactive: bool = False

    def validate_for_execution(self) -> list[str]:
        """Return a list of validation errors blocking pipeline execution."""
        errors: list[str] = []
        if not self.target.strip():
            errors.append("target is required")
        if not self.source_roots:
            errors.append("source roots are required")
        return errors
