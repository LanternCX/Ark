from pathlib import Path


def test_agents_md_exists_and_mentions_local_skills() -> None:
    content = Path("AGENTS.md").read_text(encoding="utf-8")
    assert ".opencode/skills" in content
    assert "questionary + rich" in content
    assert "litellm" in content.lower()
