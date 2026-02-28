"""Stage 1 suffix review defaults and helpers."""


def apply_default_selection(rows: list[dict], threshold: float) -> set[str]:
    """Select extensions that are keep-labeled with enough confidence."""
    selected: set[str] = set()
    for row in rows:
        if (
            row.get("label") == "keep"
            and float(row.get("confidence", 0.0)) >= threshold
        ):
            selected.add(str(row["ext"]))
    return selected
