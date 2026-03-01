from pathlib import Path


def test_readme_mentions_minimal_metadata_boundary() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "basename" in content
    assert "parent_dir_name" in content
    assert "no file content" in content.lower()


def test_readme_mentions_runtime_rules_preferences_boundary() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "<runtime-root>/rules.md" in content
    assert "does not change output json schema" in content.lower()


def test_readme_clarifies_rules_text_can_be_in_remote_prompts() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert (
        "may include this explicit user-provided text in remote ai prompts"
        in content.lower()
    )
    assert (
        "no file content means scanned source files being backed up" in content.lower()
    )


def test_privacy_boundary_doc_mentions_rules_prompt_scope() -> None:
    content = Path("docs/privacy-boundary.md").read_text(encoding="utf-8")
    assert "<runtime-root>/rules.md" in content
    assert (
        "may include this explicit user-provided text in remote ai prompts"
        in content.lower()
    )
    assert (
        "no file content means scanned source files being backed up" in content.lower()
    )


def test_readme_zh_mentions_runtime_rules_file_parity() -> None:
    content = Path("README.zh-CN.md").read_text(encoding="utf-8")
    assert "<运行目录>/rules.md" in content
    assert "远程 llm 调用开启时" in content.lower()
    assert "不上传文件内容" in content
    assert "被扫描并准备备份的源文件内容" in content


def test_architecture_doc_mentions_privacy_boundary_wording() -> None:
    content = Path("docs/architecture.md").read_text(encoding="utf-8")
    assert "<runtime-root>/rules.md" in content
    assert "does not change the output json schema contract" in content.lower()
    assert "no file content" in content.lower()
    assert "scanned source files being backed up" in content.lower()


def test_architecture_zh_doc_mentions_privacy_boundary_wording() -> None:
    content = Path("docs/architecture.zh-CN.md").read_text(encoding="utf-8")
    assert "<运行目录>/rules.md" in content
    assert "不改变输出 json schema 合同" in content.lower()
    assert "不会发送文件内容" in content
    assert "被扫描并准备备份的源文件内容" in content


def test_readme_mentions_two_user_visible_stages_only() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "Stage 1: Suffix Screening" in content
    assert "Stage 2: Final Review and Backup" in content
    assert "Stage 2: Path Tiering" not in content
    assert "Stage 3: Final Review and Backup" not in content


def test_readme_mentions_final_review_includes_all_files() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "includes all scanned files" in content.lower()
    assert "filtered by stage 1" in content.lower()
    assert "matched by ignore rules" in content.lower()


def test_readme_zh_mentions_two_user_visible_stages_only() -> None:
    content = Path("README.zh-CN.md").read_text(encoding="utf-8")
    assert "Stage 1: Suffix Screening" in content
    assert "Stage 2: Final Review and Backup" in content
    assert "Stage 2: Path Tiering" not in content
    assert "Stage 3: Final Review and Backup" not in content


def test_architecture_mentions_internal_tiering_hidden_from_user_stage() -> None:
    content = Path("docs/architecture.md").read_text(encoding="utf-8")
    assert "internal tiering" in content.lower()
    assert "not shown as a user stage" in content.lower()
