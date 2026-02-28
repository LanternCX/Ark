from rich.console import Console

from ark.tui.stage1_review import (
    SuffixReviewRow,
    _default_checkbox_prompt,
    apply_default_selection,
    classify_suffix_category,
    flatten_grouped_suffix_choices,
    group_suffix_rows,
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
        assert len(choices) >= 4
        assert choices[0]["value"].startswith("header::")
        assert choices[2]["value"].startswith("header::")
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


def test_group_suffix_rows_uses_category_layering() -> None:
    rows = [
        SuffixReviewRow(
            ext=".pdf",
            label="keep",
            tag="document",
            confidence=0.9,
            reason="doc",
        ),
        SuffixReviewRow(
            ext=".jpg",
            label="keep",
            tag="media",
            confidence=0.8,
            reason="image",
        ),
        SuffixReviewRow(
            ext=".tmp",
            label="drop",
            tag="cache",
            confidence=0.7,
            reason="cache",
        ),
    ]

    grouped = group_suffix_rows(rows)

    assert "Document" in grouped
    assert "Image" in grouped
    assert "Temp/Cache" in grouped
    assert grouped["Document"][0].ext == ".pdf"


def test_flatten_grouped_suffix_choices_includes_category_headers() -> None:
    rows = [
        SuffixReviewRow(
            ext=".pdf",
            label="keep",
            tag="document",
            confidence=0.9,
            reason="doc",
        )
    ]

    choices = flatten_grouped_suffix_choices(group_suffix_rows(rows))

    assert len(choices) >= 2
    assert choices[0]["value"].startswith("header::")
    assert "Document" in choices[0]["name"]
    assert choices[1]["value"] == ".pdf"


def test_classify_suffix_category_assigns_expected_buckets() -> None:
    assert classify_suffix_category(".pdf") == "Document"
    assert classify_suffix_category(".jpg") == "Image"
    assert classify_suffix_category(".tmp") == "Temp/Cache"
