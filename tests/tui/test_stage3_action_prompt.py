from prompt_toolkit.keys import Keys

import ark.tui.stage3_review as stage3_review


def test_default_action_prompt_registers_eager_exit_bindings(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeApplication:
        def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            captured["key_bindings"] = kwargs["key_bindings"]

        def run(self) -> str:
            return "done"

    monkeypatch.setattr(stage3_review, "Application", FakeApplication)

    result = stage3_review._default_action_prompt(
        "msg",
        [{"name": "item", "value": "node::/root"}],
    )

    assert result == "done"
    key_bindings = captured["key_bindings"]
    bindings = getattr(key_bindings, "bindings")
    eager_by_key = {binding.keys: type(binding.eager).__name__ for binding in bindings}
    assert eager_by_key[("q",)] == "Always"
    assert eager_by_key[(Keys.Escape,)] == "Always"


def test_tree_action_hint_mentions_done_shortcuts() -> None:
    assert "q/esc=done" in stage3_review._TREE_ACTION_HINT
    assert "Enter=select" in stage3_review._TREE_ACTION_HINT
