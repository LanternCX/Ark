from ark.pipeline.run_backup import run_backup_pipeline


def test_run_backup_pipeline_uses_stage_reviews() -> None:
    stage1_called = False
    stage3_called = False

    def fake_stage1_review(rows):
        nonlocal stage1_called
        stage1_called = True
        assert rows
        return {".pdf", ".docx"}

    def fake_stage3_review(rows):
        nonlocal stage3_called
        stage3_called = True
        assert rows
        return {rows[0].path}

    logs = run_backup_pipeline(
        target="X:/ArkBackup",
        dry_run=True,
        stage1_review_fn=fake_stage1_review,
        stage3_review_fn=fake_stage3_review,
    )

    assert stage1_called is True
    assert stage3_called is True
    assert any("Whitelist size: 2" in line for line in logs)
    assert any("Selected paths: 1" in line for line in logs)
