from rich.console import Console
from prompt_toolkit.keys import Keys
from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

import src.tui.stage1_review as stage1_review

from src.tui.stage1_review import (
    SuffixReviewRow,
    _default_checkbox_prompt,
    _marker_for_state,
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
        assert any(item["value"].startswith("category::") for item in choices)
        assert ".pdf" in default
        assert ".tmp" not in default
        assert len(choices) >= 3
        return default

    whitelist = run_stage1_review(
        rows,
        threshold=0.8,
        checkbox_prompt=fake_checkbox,
        console=Console(record=True),
    )
    assert whitelist == {".pdf"}


def test_run_stage1_review_supports_category_level_selection() -> None:
    rows = [
        SuffixReviewRow(
            ext=".pdf", label="keep", tag="document", confidence=0.9, reason="doc"
        ),
        SuffixReviewRow(
            ext=".jpg", label="keep", tag="image", confidence=0.9, reason="image"
        ),
        SuffixReviewRow(
            ext=".tmp", label="drop", tag="cache", confidence=0.9, reason="temp"
        ),
    ]

    def fake_checkbox(
        message: str, choices: list[dict], default: list[str]
    ) -> list[str]:
        assert "Suffix whitelist" in message
        values = {item.get("value") for item in choices}
        assert "category::Document" in values
        assert "category::Image" in values
        return ["category::Document", ".jpg"]

    whitelist = run_stage1_review(
        rows, checkbox_prompt=fake_checkbox, console=Console(record=True)
    )
    assert whitelist == {".pdf", ".jpg"}


def test_run_stage1_review_expands_category_selection_to_all_suffixes() -> None:
    rows = [
        SuffixReviewRow(
            ext=".pdf", label="keep", tag="document", confidence=0.9, reason="doc"
        ),
        SuffixReviewRow(
            ext=".docx", label="keep", tag="document", confidence=0.9, reason="doc"
        ),
        SuffixReviewRow(
            ext=".tmp", label="drop", tag="cache", confidence=0.1, reason="temp"
        ),
    ]

    whitelist = run_stage1_review(
        rows,
        checkbox_prompt=lambda _message, _choices, _default: ["category::Document"],
        console=Console(record=True),
    )

    assert whitelist == {".pdf", ".docx"}


def test_default_checkbox_prompt_sets_checked_choices(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeApplication:
        def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            captured["key_bindings"] = kwargs["key_bindings"]

        def run(self) -> list[str]:
            return [".pdf"]

    monkeypatch.setattr(stage1_review, "Application", FakeApplication)

    result = _default_checkbox_prompt(
        message="Suffix whitelist selection",
        choices=[
            {"name": "pdf", "value": ".pdf"},
            {"name": "tmp", "value": ".tmp"},
        ],
        default=[".pdf"],
    )

    assert result == [".pdf"]
    key_bindings = captured["key_bindings"]
    bindings = getattr(key_bindings, "bindings")
    eager_by_key = {binding.keys: type(binding.eager).__name__ for binding in bindings}
    assert eager_by_key[("q",)] == "Always"
    assert eager_by_key[(Keys.Escape,)] == "Always"


def test_default_checkbox_prompt_returns_empty_on_empty_choices() -> None:
    result = _default_checkbox_prompt(
        message="empty",
        choices=[],
        default=[],
    )

    assert result == []


def test_default_checkbox_prompt_allows_q_to_finish_prompt() -> None:
    with create_pipe_input() as pipe_input:
        pipe_input.send_text("q")
        with create_app_session(input=pipe_input, output=DummyOutput()):
            result = _default_checkbox_prompt(
                message="Suffix whitelist selection",
                choices=[{"name": "pdf", "value": ".pdf"}],
                default=[],
            )

    assert result == []


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


def test_marker_for_state_uses_symbolic_semantics() -> None:
    assert _marker_for_state(selected_count=0, total_count=2) == "\u25cb"
    assert _marker_for_state(selected_count=1, total_count=2) == "\u25d0"
    assert _marker_for_state(selected_count=2, total_count=2) == "\u25cf"


def test_run_stage1_review_uses_symbolic_category_and_suffix_rows() -> None:
    rows = [
        SuffixReviewRow(
            ext=".pdf",
            label="keep",
            tag="document",
            confidence=0.95,
            reason="doc",
        ),
        SuffixReviewRow(
            ext=".tmp",
            label="drop",
            tag="cache",
            confidence=0.2,
            reason="temp",
        ),
    ]

    captured: dict[str, list[dict]] = {}

    def fake_checkbox(
        _message: str, choices: list[dict], default: list[str]
    ) -> list[str]:
        captured["choices"] = choices
        return default

    run_stage1_review(
        rows,
        threshold=0.8,
        checkbox_prompt=fake_checkbox,
        console=Console(record=True),
    )

    category_row = next(
        item
        for item in captured["choices"]
        if str(item["value"]).startswith("category::")
    )
    suffix_row = next(item for item in captured["choices"] if item["value"] == ".pdf")

    assert "\U0001f4c1" in str(category_row["name"])
    assert "\U0001f4c4" in str(suffix_row["name"])
    assert any(
        symbol in str(category_row["name"]) for symbol in ("\u25cb", "\u25d0", "\u25cf")
    )
