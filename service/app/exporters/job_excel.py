# root/service/app/exporters/job_excel.py
"""Excel exporter for job items (flow-agnostic)."""
# Why: reuse the same table-shaping rules for UI and downloads.

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from typing import Any, cast

import xlsxwriter
from sqlalchemy.orm import Session

from ...db.models import Job, JobItem
from ..utils.jinja_filters import format_tz
from ..utils.job_rows import build_rows_for_items
from ..utils.nested_numbering import render_numbered_text
from ..utils.table_shape import build_table


def _cell_to_excel_value(value: Any) -> Any:
    """Convert a shaped cell value into an Excel-friendly scalar.

    This follows dynamic_cell.html logic:

    - strings and numbers: used as-is
    - mappings and sequences: rendered as numbered multi-line text
    - None: rendered as a small dash
    - everything else: stringified
    """
    if value is None:
        return "-"
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping) or (
        isinstance(value, Sequence) and not isinstance(value, (str, bytes))
    ):
        # Use shared numbering rules for complex values.
        return render_numbered_text(value)
    return str(value)


def build_job_excel_bytes(job: Job, items: list[JobItem]) -> bytes:
    """Render one .xlsx file for a job using dynamic columns."""
    rows = build_rows_for_items(items)
    columns, shaped = build_table(rows)

    if not columns:
        # Fallback for empty jobs; keep a minimal shape.
        columns = ["status", "timings"]

    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    worksheet = workbook.add_worksheet("items")

    meta_fmt = workbook.add_format({"italic": True})
    header_fmt = workbook.add_format({"bold": True, "text_wrap": True, "border": 1})
    cell_fmt = workbook.add_format({"text_wrap": True, "border": 1})

    # Row 0: job meta, using the same timezone rules as the UI.
    created_at = getattr(job, "created_at", None)
    finished_at = getattr(job, "finished_at", None)

    meta_parts: list[str] = [
        f"Job: {job.id}",
        f"Flow: {job.flow_type}",
        f"Status: {job.status}",
        f"Created: {format_tz(created_at)}",
        f"Finished: {format_tz(finished_at)}",
    ]
    meta_text = " | ".join(meta_parts)

    last_col_idx = max(len(columns) - 1, 0)
    worksheet.merge_range(0, 0, 0, last_col_idx, meta_text, meta_fmt)

    # Row 1: headers.
    for col_idx, name in enumerate(columns):
        worksheet.write(1, col_idx, name, header_fmt)

    # Row 2+: data rows shaped by the same rules as the UI.
    for row_idx, row in enumerate(shaped, start=2):
        for col_idx, name in enumerate(columns):
            worksheet.write(
                row_idx,
                col_idx,
                _cell_to_excel_value(row.get(name)),
                cell_fmt,
            )

    # Add table styling on top of header + data.
    last_row_idx = 1 + len(shaped)
    worksheet.add_table(
        1,
        0,
        last_row_idx,
        last_col_idx,
        {"columns": [{"header": col} for col in columns]},
    )

    # Simple column sizing for readability at a glance.
    for col_idx, name in enumerate(columns):
        width = max(len(str(name)), 12) + 4
        worksheet.set_column(col_idx, col_idx, width)

    workbook.close()
    buffer.seek(0)
    return buffer.getvalue()


def build_job_excel_from_db(db: Session, job_id: str) -> tuple[Job, bytes]:
    """Load one job and its items, then build Excel bytes."""
    job: Job | None = db.get(Job, job_id)
    if job is None:
        raise ValueError("job_not_found")

    raw_items = db.query(JobItem).filter(JobItem.job_id == job_id).order_by(JobItem.idx.asc()).all()
    items = cast(list[JobItem], cast(object, raw_items))

    content = build_job_excel_bytes(job, items)
    return job, content
