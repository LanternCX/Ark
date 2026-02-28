from rich.console import Console

from ark.tui.stage1_review import (
    SuffixReviewRow,
    _default_checkbox_prompt,
    apply_default_selection,
    run_stage1_review,
)


def test_apply_default_selection_keeps_high_confidence_keep_labels() -> None:
    rows = [{"ext": ".pdf", "label": "keep", "confidence": 0.95}]
    selected = apply_default_selection(rows, threshold=0.8)
    assert ".pdf" in selected


def test_run_stage1_review_uses_default_whitelist() -> None:
    rows = [
        SuffixReviewRow(
            ext=".pdf",
            label="keep",
            tag="document",
            confidence=0.93,
            reason="Likely personal document",
        ),
        SuffixReviewRow(
            ext=".tmp",
            label="drop",
            tag="cache",
            confidence=0.91,
            reason="Likely temporary artifact",
        ),
    ]

    def fake_checkbox(
        message: str, choices: list[dict], default: list[str]
    ) -> list[str]:
        assert "Suffix whitelist" in message
        assert ".pdf" in default
        assert ".tmp" not in default
        assert len(choices) == 2
        return default

    whitelist = run_stage1_review(
        rows,
        threshold=0.8,
        checkbox_prompt=fake_checkbox,
        console=Console(record=True),
    )
    assert whitelist == {".pdf"}


def test_default_checkbox_prompt_sets_checked_choices(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakePrompt:
        def ask(self) -> list[str]:
            return [".pdf"]

    def fake_checkbox(**kwargs):
        captured.update(kwargs)
        return FakePrompt()

    monkeypatch.setattr("ark.tui.stage1_review.questionary.checkbox", fake_checkbox)

    result = _default_checkbox_prompt(
        message="Suffix whitelist selection",
        choices=[
            {"name": "pdf", "value": ".pdf"},
            {"name": "tmp", "value": ".tmp"},
        ],
        default=[".pdf"],
    )

    assert result == [".pdf"]
    assert "default" not in captured
    assert captured["choices"][0]["checked"] is True
    assert captured["choices"][1].get("checked") is not True
