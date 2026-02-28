from pathlib import Path


def test_readme_mentions_minimal_metadata_boundary() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "basename" in content
    assert "parent_dir_name" in content
    assert "no file content" in content.lower()
