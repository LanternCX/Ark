from pathlib import Path


def test_project_skills_are_under_opencode() -> None:
    root = Path(".opencode") / "skills"
    assert (root / "code-standard" / "SKILL.md").exists()
    assert (root / "doc-maintainer" / "SKILL.md").exists()
    assert (root / "git-workflow" / "SKILL.md").exists()
