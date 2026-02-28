from ark.tui.stage1_review import apply_default_selection


def test_apply_default_selection_keeps_high_confidence_keep_labels() -> None:
    rows = [{"ext": ".pdf", "label": "keep", "confidence": 0.95}]
    selected = apply_default_selection(rows, threshold=0.8)
    assert ".pdf" in selected
