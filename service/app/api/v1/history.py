# root/service/app/api/v1/history.py
"""History list (jobs summary) with paging & fields projection."""
# Why: avoid heavy payloads; cursor/page kept simple for phase 1.

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from service.app.deps import get_db, get_settings, require_api_key
from service.app.utils.jinja_filters import format_tz
from service.db.models import Job

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("")
def list_jobs(
    page: int = Query(1, ge=1),
    limit: int | None = Query(None, ge=1, le=1000),
    flow_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    tz: str = Query("Asia/Ho_Chi_Minh"),
) -> list[dict[str, Any]]:
    """Return job summaries page; default limit via env."""
    s = get_settings()
    per_page = limit or s.page_size_default
    if per_page > s.page_size_max:
        per_page = s.page_size_max

    stmt = select(Job).order_by(desc(Job.created_at))
    if flow_type:
        stmt = stmt.filter(Job.flow_type == flow_type)
    if status:
        stmt = stmt.filter(Job.status == status)
    rows = db.execute(stmt.limit(per_page).offset((page - 1) * per_page)).scalars().all()
    return [
        {
            "id": str(r.id),
            "flow_type": r.flow_type,
            "status": r.status,
            "created_at": format_tz(r.created_at, tz=tz),
            "finished_at": format_tz(r.finished_at, tz=tz),
            "counts": {
                "done": r.count_done,
                "failed": r.count_failed,
                "cancelled": r.count_cancelled,
            },
        }
        for r in rows
    ]
