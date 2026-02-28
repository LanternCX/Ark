from rich.console import Console

from ark.tui.stage3_review import PathReviewRow, run_stage3_review


def test_run_stage3_review_supports_tree_navigation_and_directory_toggle() -> None:
    rows = [
        PathReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        ),
        PathReviewRow(
            path="/root/docs/b.txt",
            tier="tier2",
            size_bytes=10,
            reason="low value",
            confidence=0.3,
            ai_risk="low_value",
        ),
        PathReviewRow(
            path="/root/media/c.jpg",
            tier="tier2",
            size_bytes=10,
            reason="photo",
            confidence=0.8,
        ),
    ]

    actions = iter(
        [
            "enter::/root",
            "toggle::/root/docs",
            "done",
        ]
    )

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        values = {item["value"] for item in choices}
        selected = next(actions)
        assert selected in values
        return selected

    selected = run_stage3_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    assert selected == {"/root/docs/a.txt", "/root/docs/b.txt"}


def test_run_stage3_review_hides_low_value_only_branches_by_default() -> None:
    rows = [
        PathReviewRow(
            path="/root/keep/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        ),
        PathReviewRow(
            path="/root/trash/a.tmp",
            tier="tier2",
            size_bytes=10,
            reason="cache",
            confidence=0.2,
            ai_risk="low_value",
        ),
    ]
    actions = iter(["done"])
    seen_choices: list[list[str]] = []

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        seen_choices.append([item["value"] for item in choices])
        return next(actions)

    selected = run_stage3_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    assert selected == {"/root/keep/a.txt"}
    flattened = {value for page in seen_choices for value in page}
    assert "enter::/root/trash" not in flattened


def test_run_stage3_review_can_show_low_value_branches_from_start() -> None:
    rows = [
        PathReviewRow(
            path="/root/trash/a.tmp",
            tier="tier2",
            size_bytes=10,
            reason="cache",
            confidence=0.2,
            ai_risk="low_value",
        )
    ]
    actions = iter(["enter::/root", "done"])
    seen_choices: list[list[str]] = []

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        seen_choices.append([item["value"] for item in choices])
        return next(actions)

    run_stage3_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
        hide_low_value_default=False,
    )

    flattened = {value for page in seen_choices for value in page}
    assert "enter::/root/trash" in flattened
