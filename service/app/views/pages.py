# root/service/app/views/pages.py
"""Pages (Jinja/HTMX): role home, dashboard, flow host, job detail."""
# Why: keep UI small, data-driven via registries.

from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import Response

from ...db.models import Job, JobItem
from ..deps import get_db, get_settings, templates
from ..registry.bdd_map import BDD_ENTRIES
from ..registry.form_registry import get_flow_by_slug

router = APIRouter()


@router.get("/")
def home(request: Request) -> Response:
    """Homepage listing roles for role-based navigation."""
    roles = sorted({(e.role, e.role_slug) for e in BDD_ENTRIES})
    return templates.TemplateResponse(
        "pages/bdd_home.html", {"request": request, "roles": roles, "entries": BDD_ENTRIES}
    )


@router.get("/dashboard/{role_slug}")
def dashboard(request: Request, role_slug: str) -> Response:
    """Role dashboard: project→features mapping."""
    feats = [e for e in BDD_ENTRIES if e.role_slug == role_slug]
    if not feats:
        raise HTTPException(404, "role_not_found")
    projects = sorted({e.project for e in feats})
    return templates.TemplateResponse(
        "pages/bdd_dashboard.html",
        {
            "request": request,
            "role": feats[0].role,
            "role_slug": role_slug,
            "projects": projects,
            "entries": feats,
        },
    )


@router.get("/flows/{flow_slug}")
def flow_host(
    request: Request,
    flow_slug: str,
) -> Response:
    fm = get_flow_by_slug(flow_slug)
    return templates.TemplateResponse(
        "pages/flow_host.html",
        {
            "request": request,
            "form_tpl": fm.template_path,
            "flow_slug": flow_slug,
        },
    )


@router.get("/jobs/{job_id}")
def job_detail(
    request: Request,
    job_id: str,
    s: Annotated[Any, Depends(get_settings)],
    db: Session = Depends(get_db),
) -> Response:
    job: Job | None = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job_not_found")

    # Counters
    qs = db.query(JobItem).filter(JobItem.job_id == job_id)
    cnt_done = qs.filter(JobItem.status == "DONE").count()
    cnt_failed = qs.filter(JobItem.status == "FAILED").count()
    cnt_cancelled = qs.filter(JobItem.status == "CANCELLED").count()

    poll_ms = int(os.getenv("AUTOSUITE_UI_POLL_MS", str(s.ui_poll_ms)))
    return templates.TemplateResponse(
        "pages/job_detail.html",
        {
            "request": request,
            "job": job,
            "poll_ms": poll_ms,
            "counts": {"done": cnt_done, "failed": cnt_failed, "cancelled": cnt_cancelled},
        },
    )


@router.get("/history")
def history(
    request: Request,
    s: Annotated[Any, Depends(get_settings)],
) -> Response:
    """History: list jobs with pagination."""
    return templates.TemplateResponse(
        "pages/history.html",
        {
            "request": request,
            "poll_ms": s.ui_poll_ms,
            "default_page_size": s.page_size_default,
        },
    )
