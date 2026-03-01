from src.tui.tree_selection import SelectionState, TreeSelectionState, paginate_items


def test_directory_is_partial_when_only_some_children_selected() -> None:
    state = TreeSelectionState.from_paths(
        [
            "/data/docs/a.txt",
            "/data/docs/b.txt",
            "/data/media/c.jpg",
        ],
        selected_files={"/data/docs/a.txt"},
    )

    assert state.selection_state("/data/docs") == SelectionState.PARTIAL
    assert state.selection_state("/data/docs/a.txt") == SelectionState.CHECKED
    assert state.selection_state("/data/docs/b.txt") == SelectionState.UNCHECKED


def test_toggle_directory_recursively_selects_and_unselects_descendants() -> None:
    state = TreeSelectionState.from_paths(
        [
            "/data/docs/a.txt",
            "/data/docs/b.txt",
            "/data/media/c.jpg",
        ]
    )

    state.toggle("/data/docs")
    assert state.selected_files == {"/data/docs/a.txt", "/data/docs/b.txt"}
    assert state.selection_state("/data/docs") == SelectionState.CHECKED

    state.toggle("/data/docs")
    assert state.selected_files == set()
    assert state.selection_state("/data/docs") == SelectionState.UNCHECKED


def test_paginate_items_slices_current_page_items() -> None:
    items = [f"item-{idx}" for idx in range(1, 8)]

    page2, total_pages = paginate_items(items, page_size=3, page_index=1)

    assert total_pages == 3
    assert page2 == ["item-4", "item-5", "item-6"]
