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


def test_package_workflow_builds_windows_and_macos() -> None:
    content = Path(".github/workflows/package.yml").read_text(encoding="utf-8")
    assert "windows-latest" in content
    assert "macos-latest" in content


def test_package_workflow_bundles_runtime_config_and_rules() -> None:
    content = Path(".github/workflows/package.yml").read_text(encoding="utf-8")
    assert "main.py" in content
    assert ".ark/config.json" in content
    assert "src/rules/baseline.ignore" in content
    assert "src/rules/suffix_rules.toml" in content


def test_main_entrypoint_exists() -> None:
    assert Path("main.py").exists()
