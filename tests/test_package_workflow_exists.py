from pathlib import Path


def test_package_workflow_exists() -> None:
    workflow = Path(".github/workflows/package.yml")
    assert workflow.exists()


def test_package_workflow_has_tag_trigger_and_release() -> None:
    content = Path(".github/workflows/package.yml").read_text(encoding="utf-8")
    assert "tags:" in content
    assert "- 'v*'" in content
    assert "workflow_dispatch:" in content
    assert "action-gh-release" in content
    assert "draft: true" in content
