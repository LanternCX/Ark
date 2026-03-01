from rich.console import Console
import threading
import time

from src.tui.final_review import FinalReviewRow, run_final_review


def test_run_final_review_supports_tree_navigation_and_directory_toggle() -> None:
    rows = [
        FinalReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        ),
        FinalReviewRow(
            path="/root/docs/b.txt",
            tier="tier2",
            size_bytes=10,
            reason="low value",
            confidence=0.3,
            ai_risk="low_value",
        ),
        FinalReviewRow(
            path="/root/media/c.jpg",
            tier="tier2",
            size_bytes=10,
            reason="photo",
            confidence=0.8,
        ),
    ]

    actions = iter(
        [
            "enter::node::/root",
            "space::node::/root/docs",
            "done",
        ]
    )

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        selected = next(actions)
        if selected.startswith(("enter::", "space::")):
            value = selected.split("::", 1)[1]
            assert value in {item["value"] for item in choices}
        return selected

    selected = run_final_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    assert selected == {"/root/docs/a.txt", "/root/docs/b.txt"}


def test_run_final_review_hides_low_value_only_branches_by_default() -> None:
    rows = [
        FinalReviewRow(
            path="/root/keep/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        ),
        FinalReviewRow(
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

    selected = run_final_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    assert selected == {"/root/keep/a.txt"}
    flattened = {value for page in seen_choices for value in page}
    assert "node::/root/trash" not in flattened


def test_run_final_review_can_show_low_value_branches_from_start() -> None:
    rows = [
        FinalReviewRow(
            path="/root/trash/a.tmp",
            tier="tier2",
            size_bytes=10,
            reason="cache",
            confidence=0.2,
            ai_risk="low_value",
        )
    ]
    actions = iter(["enter::node::/root", "done"])
    seen_choices: list[list[str]] = []

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        seen_choices.append([item["value"] for item in choices])
        return next(actions)

    run_final_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
        hide_low_value_default=False,
    )

    flattened = {value for page in seen_choices for value in page}
    assert "node::/root/trash" in flattened


def test_run_final_review_uses_tree_symbolic_choices_instead_of_verbs() -> None:
    rows = [
        FinalReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        )
    ]
    captured_names: list[str] = []

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        captured_names.extend([str(item["name"]) for item in choices])
        return "done"

    run_final_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    joined = "\n".join(captured_names)
    assert "Toggle folder" not in joined
    assert "Open folder" not in joined
    assert "Toggle file" not in joined
    assert any(name.startswith(("●", "◐", "○", "▸", "▾")) for name in captured_names)


def test_run_final_review_renders_each_folder_once() -> None:
    rows = [
        FinalReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        )
    ]
    captured_names: list[str] = []

    actions = iter(["enter::node::/root", "done"])

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        captured_names.extend([str(item["name"]) for item in choices])
        return next(actions)

    run_final_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    docs_rows = [name for name in captured_names if "docs/" in name]
    assert len(docs_rows) == 1


def test_run_final_review_exposes_control_rows_for_enter_navigation() -> None:
    rows = [
        FinalReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        )
    ]
    captured_values: list[str] = []

    actions = iter(
        [
            "enter::node::/root",
            "enter::node::/root/docs",
            "enter::control::up",
            "enter::control::done",
        ]
    )

    def fake_action_prompt(_message: str, choices: list[dict]) -> str:
        captured_values.extend([str(item["value"]) for item in choices])
        selected = next(actions)
        if selected.startswith("enter::"):
            value = selected.split("::", 1)[1]
            assert value in {item["value"] for item in choices}
        return selected

    selected = run_final_review(
        rows,
        action_prompt=fake_action_prompt,
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
    )

    assert selected == {"/root/docs/a.txt"}
    assert "control::done" in captured_values
    assert "control::up" in captured_values


def test_run_final_review_applies_ai_dfs_drop_recursively() -> None:
    rows = [
        FinalReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        ),
        FinalReviewRow(
            path="/root/docs/sub/b.txt",
            tier="tier1",
            size_bytes=10,
            reason="doc",
            confidence=0.9,
        ),
        FinalReviewRow(
            path="/root/keep/c.txt",
            tier="tier2",
            size_bytes=10,
            reason="keep",
            confidence=0.9,
        ),
    ]

    visited: list[str] = []

    def fake_ai_directory_decision(
        directory: str,
        child_directories: list[str],
        sample_files: list[str],
    ) -> dict[str, object]:
        del child_directories, sample_files
        visited.append(directory)
        if directory == "/root/docs":
            return {"decision": "drop", "reason": "generated", "confidence": 0.9}
        if directory == "/root/keep":
            return {"decision": "keep", "reason": "important", "confidence": 0.9}
        return {"decision": "not_sure", "reason": "root", "confidence": 0.5}

    selected = run_final_review(
        rows,
        action_prompt=lambda _m, _c: "done",
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
        ai_directory_decision_fn=fake_ai_directory_decision,
    )

    assert "/root" in visited
    assert "/root/docs" in visited
    assert "/root/docs/sub" in visited
    assert selected == {"/root/keep/c.txt"}


def test_run_final_review_ai_dfs_requests_sibling_directories_concurrently() -> None:
    rows = [
        FinalReviewRow(
            path="/root/a/file.txt",
            tier="tier1",
            size_bytes=1,
            reason="a",
            confidence=0.9,
        ),
        FinalReviewRow(
            path="/root/b/file.txt",
            tier="tier1",
            size_bytes=1,
            reason="b",
            confidence=0.9,
        ),
        FinalReviewRow(
            path="/root/c/file.txt",
            tier="tier1",
            size_bytes=1,
            reason="c",
            confidence=0.9,
        ),
    ]

    lock = threading.Lock()
    active = {"count": 0, "max": 0}

    def fake_ai_directory_decision(
        directory: str,
        child_directories: list[str],
        sample_files: list[str],
    ) -> dict[str, object]:
        del child_directories, sample_files
        with lock:
            active["count"] += 1
            active["max"] = max(active["max"], active["count"])
        time.sleep(0.05)
        with lock:
            active["count"] -= 1
        if directory == "/root":
            return {"decision": "not_sure", "reason": "root", "confidence": 0.5}
        return {"decision": "keep", "reason": "leaf", "confidence": 0.9}

    run_final_review(
        rows,
        action_prompt=lambda _m, _c: "done",
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
        ai_directory_decision_fn=fake_ai_directory_decision,
    )

    assert active["max"] > 1


def test_run_final_review_ai_dfs_does_not_auto_select_manual_only_paths() -> None:
    rows = [
        FinalReviewRow(
            path="/root/docs/a.txt",
            tier="tier1",
            size_bytes=1,
            reason="doc",
            confidence=0.9,
            internal_candidate=True,
        ),
        FinalReviewRow(
            path="/root/ignored/manual.txt",
            tier="ignored",
            size_bytes=1,
            reason="manual",
            confidence=0.0,
            internal_candidate=False,
        ),
    ]

    def fake_ai_directory_decision(
        _directory: str,
        _child_directories: list[str],
        _sample_files: list[str],
    ) -> dict[str, object]:
        return {"decision": "keep", "reason": "prefer keep", "confidence": 0.9}

    selected = run_final_review(
        rows,
        action_prompt=lambda _m, _c: "done",
        confirm_prompt=lambda _msg, _default: True,
        console=Console(record=True),
        ai_directory_decision_fn=fake_ai_directory_decision,
    )

    assert "/root/docs/a.txt" in selected
    assert "/root/ignored/manual.txt" not in selected
