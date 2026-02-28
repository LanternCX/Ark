from rich.console import Console

from ark.tui.stage3_review import (
    PathReviewRow,
    _default_checkbox_prompt,
    run_stage3_review,
)


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


def test_default_checkbox_prompt_sets_checked_choices(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakePrompt:
        def ask(self) -> list[str]:
            return ["C:/Users/me/Documents/report.pdf"]

    def fake_checkbox(**kwargs):
        captured.update(kwargs)
        return FakePrompt()

    monkeypatch.setattr("ark.tui.stage3_review.questionary.checkbox", fake_checkbox)

    result = _default_checkbox_prompt(
        message="Final backup selection",
        choices=[
            {"name": "tier1", "value": "C:/Users/me/Documents/report.pdf"},
            {"name": "tier2", "value": "C:/Users/me/Downloads/archive.zip"},
        ],
        default=["C:/Users/me/Documents/report.pdf"],
    )

    assert result == ["C:/Users/me/Documents/report.pdf"]
    assert "default" not in captured
    assert captured["choices"][0]["checked"] is True
    assert captured["choices"][1].get("checked") is not True
