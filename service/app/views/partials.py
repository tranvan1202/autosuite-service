# root/service/app/views/partials.py

"""HTMX partials for live sections (items table, etc.)."""

# Why: keep polling HTML partials apart from JSON API.

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import Response

from ...db.models import Job, JobItem
from ..deps import get_db, require_api_key, templates
from ..utils.job_rows import build_rows_for_items
from ..utils.table_shape import build_table

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/jobs/{job_id}/items")
def job_items_tbody(
    request: Request,
    job_id: str,
    db: Session = Depends(get_db),
) -> Response:
    job: Job | None = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job_not_found")

    # Fetch items rows as dicts.
    q = db.query(JobItem).filter(JobItem.job_id == job_id).order_by(JobItem.id.asc())
    raw_items = q.all()
    items = cast(list[JobItem], cast(object, raw_items))

    rows = build_rows_for_items(items)
    columns, shaped = build_table(rows)

    return templates.TemplateResponse(
        "components/items_table.html",
        {
            "request": request,
            "columns": columns,
            "rows": shaped,
            "job": job,
        },
    )
