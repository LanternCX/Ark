from rich.console import Console

from ark.tui.stage3_review import PathReviewRow, run_stage3_review


def test_run_stage3_review_defaults_to_tier1_only() -> None:
    rows = [
        PathReviewRow(
            path="C:/Users/me/Documents/report.pdf",
            tier="tier1",
            size_bytes=1024,
            reason="Personal document",
            confidence=0.93,
        ),
        PathReviewRow(
            path="C:/Users/me/Downloads/archive.zip",
            tier="tier2",
            size_bytes=2048,
            reason="Potentially useful archive",
            confidence=0.61,
        ),
    ]

    def fake_checkbox(
        message: str, choices: list[dict], default: list[str]
    ) -> list[str]:
        assert "Final backup selection" in message
        assert rows[0].path in default
        assert rows[1].path not in default
        return default

    def fake_confirm(message: str, default: bool) -> bool:
        assert "Proceed with backup" in message
        assert default is True
        return True

    selected = run_stage3_review(
        rows,
        checkbox_prompt=fake_checkbox,
        confirm_prompt=fake_confirm,
        console=Console(record=True),
    )
    assert selected == {rows[0].path}
