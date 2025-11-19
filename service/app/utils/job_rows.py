# root/service/app/utils/job_rows.py
"""Helpers to shape JobItem rows for tables and exports."""
# Why: keep table row shaping in one place for UI and reports.

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ...db.models import JobItem


def build_rows_for_items(items: Iterable[JobItem]) -> list[dict[str, Any]]:
    """Convert JobItem ORM rows into generic dict rows.

    This matches the structure expected by the dynamic items table.
    """
    rows: list[dict[str, Any]] = []
    for it in items:
        rows.append(
            {
                "id": str(it.id),
                "idx": it.idx,
                "status": it.status,
                "retry_count": it.retry_count,
                "error_code": it.error_code,
                "error_message": it.error_message,
                "timings": it.timings,
                "input": it.input or {},
                "output": it.output or {},
                "extras": it.extras,
            }
        )
    return rows
