# root/service/app/utils/nested_numbering.py
"""Helpers to render nested values with numbered prefixes."""
# Why: keep nested numbering consistent across HTML and Excel.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _is_sequence(value: Any) -> bool:
    """Check if value behaves like a list but is not a plain string/bytes."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _is_mapping(value: Any) -> bool:
    """Light wrapper for Mapping check to keep intent clear."""
    return isinstance(value, Mapping)


def render_numbered_lines(value: Any, prefix: str = "") -> list[str]:
    """Render a nested structure into numbered text lines.

    Basic rules:
    - Scalars: one line with the plain value
    - Dict with one scalar value: show that child directly
    - Dict: keys are sorted, each entry gets a numeric prefix
    - Sequence: each item gets its own prefix and is rendered recursively
    """
    if not (_is_mapping(value) or _is_sequence(value)):
        return [str(value)]

    # Mapping case.
    if _is_mapping(value):
        items = list(value.items())
        if len(items) == 1 and not (_is_mapping(items[0][1]) or _is_sequence(items[0][1])):
            # Simple dict with single scalar.
            return [str(items[0][1])]

        map_lines: list[str] = []
        for idx, key in enumerate(sorted(value.keys(), key=lambda k: str(k)), start=1):
            child = value[key]
            p = f"{prefix}.{idx}" if prefix else str(idx)
            child_lines = render_numbered_lines(child, p)
            if len(child_lines) == 1:
                map_lines.append(f"{p} {key}: {child_lines[0]}")
            else:
                map_lines.append(f"{p} {key}:")
                map_lines.extend(child_lines)
        return map_lines

    # Sequence case.
    seq_lines: list[str] = []
    for idx, item in enumerate(value, start=1):
        p = f"{prefix}.{idx}" if prefix else str(idx)
        child_lines = render_numbered_lines(item, p)
        if len(child_lines) == 1:
            seq_lines.append(f"{p} {child_lines[0]}")
        else:
            seq_lines.extend(child_lines)
    return seq_lines


def render_numbered_text(value: Any, prefix: str = "") -> str:
    """Render nested value into a single multi-line string."""
    return "\n".join(render_numbered_lines(value, prefix))
