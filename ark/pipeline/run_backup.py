"""Run backup pipeline orchestration."""


def run_backup_pipeline(target: str, dry_run: bool) -> list[str]:
    """Return high-level stage logs for backup execution."""
    return [
        "Stage 1: Suffix Screening",
        "Stage 2: Path Tiering",
        "Stage 3: Final Review and Backup",
        f"Target: {target}",
        f"Dry run: {dry_run}",
    ]
