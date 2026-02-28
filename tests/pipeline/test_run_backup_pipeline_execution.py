from ark.pipeline.run_backup import run_backup_pipeline


def test_run_backup_pipeline_executes_mirror_copy_for_selected_paths(tmp_path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    src_file = src_root / "docs" / "a.txt"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("hello", encoding="utf-8")

    target = tmp_path / "backup"

    def fake_stage1_review(rows):
        return {".txt"}

    def fake_stage3_review(rows):
        return {row.path for row in rows}

    run_backup_pipeline(
        target=str(target),
        dry_run=False,
        source_roots=[src_root],
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=fake_stage3_review,
    )

    assert (target / "src" / "docs" / "a.txt").exists()
