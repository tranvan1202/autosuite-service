# root/service/app/api/v1/jobs.py
"""Jobs API: create/list/get/items/cancel."""
# Why: one router governs the whole job lifecycle (clean, testable).

from __future__ import annotations

import os
import signal
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header as HeaderParam, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus, JobStatus
from service.constants.api import Header as APIHeader

from ....db.models import Job, JobItem
from ....executor.scheduler import schedule_jobs
from ...deps import get_db, get_settings, require_api_key
from ...exporters.job_excel import build_job_excel_from_db
from ...registry.form_registry import get_flow_by_enum_name
from ...validation import prevalidate

_logger = structlog.get_logger(__name__)
router = APIRouter(dependencies=[Depends(require_api_key)])

# ---------- payloads ----------


class CreateJobPayload(BaseModel):
    """Flow-agnostic payload; items validated by flow hooks."""

    flow_type: FlowType
    items: list[dict[str, Any]] = Field(min_length=1)
    options: dict[str, Any] = Field(default_factory=dict)
    site_slugs: list[str] = Field(default_factory=list)


# ---------- helpers ----------


def _enrich_item_meta(
    idx: int, item: dict[str, Any], job_id: str, flow: FlowType
) -> dict[str, Any]:
    """Stable meta keys for FE/metrics; caller merges user meta."""
    base: dict[str, Any] = {"idx": idx}
    user_meta: dict[str, Any] = {}
    if isinstance(item, dict):
        meta = item.get("meta")
        if isinstance(meta, dict):
            user_meta = meta
    return {**base, **user_meta}


def _pretty_input_text(flow: FlowType, item: dict[str, Any]) -> str:
    """Delegate snapshot to registry when possible; keep short."""
    try:
        fm = get_flow_by_enum_name(str(flow))
        return fm.pretty_input_fn(item)
    except Exception:
        try:
            return ", ".join(f"{k}={v}" for k, v in item.items() if k != "meta")
        except Exception:
            return ""


# ---------- routes ----------


@router.post("", status_code=201)
def create_job(
    payload: CreateJobPayload,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str | None = HeaderParam(default=None, alias=APIHeader.IDEMPOTENCY_KEY.value),
) -> dict[str, Any]:
    """Create a job and try to schedule it (respecting concurrency limit).

    - Enforce max_items_per_job.
    - Enforce payload_max_bytes via Content-Length (if provided).
    - Support Idempotency-Key header to dedupe job creation.
    """
    s = get_settings()

    # Guard body size based on Content-Length (if client sends).
    length_header = request.headers.get("content-length")
    if length_header is not None:
        try:
            length = int(length_header)
        except ValueError as err:
            raise HTTPException(status_code=400, detail="invalid_content_length") from err
        if length > s.payload_max_bytes:
            raise HTTPException(status_code=413, detail="payload_too_large")

    if len(payload.items) > s.max_items_per_job:
        raise HTTPException(status_code=413, detail="too_many_items")

    raw_items: list[dict[str, Any]] = [dict(it) for it in payload.items]

    # Flow-level cheap validation (no I/O).
    val_errors = prevalidate(payload.flow_type, raw_items)
    if val_errors:
        raise HTTPException(status_code=422, detail={"errors": val_errors})

    if idempotency_key:
        job_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"job:{payload.flow_type}:{idempotency_key}",
            )
        )
    else:
        job_id = str(uuid.uuid4())

    now = datetime.now(UTC)

    try:
        db.add(
            Job(
                id=job_id,
                flow_type=str(payload.flow_type),
                status=str(JobStatus.PENDING),
                options=payload.options,
                created_at=now,
                finished_at=None,
            )
        )

        # Enrich once for both DB and runner.
        enriched_items: list[dict[str, Any]] = []
        for idx, it in enumerate(raw_items):
            d: dict[str, Any] = dict(it)
            meta = _enrich_item_meta(idx, d, job_id, payload.flow_type)
            meta["raw_text"] = (d.get("meta") or {}).get("raw_text") or _pretty_input_text(
                payload.flow_type, d
            )
            d["meta"] = meta
            enriched_items.append(d)

        # Bulk persist items (minimize ORM overhead)
        db.bulk_save_objects(
            [
                JobItem(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    idx=i,
                    status=str(ItemStatus.PENDING),
                    retry_count=0,
                    error_code=None,
                    error_message=None,
                    input=enriched_items[i],
                    output=None,
                    timings=None,
                    extras=None,
                    created_at=now,
                    finished_at=None,
                )
                for i in range(len(enriched_items))
            ]
        )
        db.commit()
    except IntegrityError as err:
        db.rollback()
        # No idempotency_key but still get IntegrityError => DB bug, to raise again.
        if not idempotency_key:
            raise

        # Has Idempotency-Key => consider primary-key conflict as "job created before".
        existing: Job | None = db.get(Job, job_id)
        if not existing:
            # Rare case: conflict but row not found => return 409 to be safe.
            raise HTTPException(status_code=409, detail="idempotency_conflict") from err

        _logger.info(
            "job_idempotent_reused",
            job_id=job_id,
            flow=existing.flow_type,
            status=existing.status,
        )
        return {
            "job_id": job_id,
            "status": existing.status,
            "items_count": len(payload.items),
        }

    # Schedule based on slots (max workers, queue is FIFO).
    schedule_jobs(db)

    _logger.info(
        "job_created",
        job_id=job_id,
        flow=str(payload.flow_type),
        items=len(raw_items),
        idempotency_key=bool(idempotency_key),
    )
    return {"job_id": job_id, "status": str(JobStatus.PENDING), "items_count": len(raw_items)}


@router.get("")
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1),
    status: str | None = None,
    flow_type: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List jobs with simple paging (FIFO)."""
    s = get_settings()
    per = page_size or s.page_size_default
    if per > s.page_size_max:
        per = s.page_size_max

    stmt = select(Job).order_by(desc(Job.created_at))
    if status:
        stmt = stmt.filter(Job.status == status)
    if flow_type:
        stmt = stmt.filter(Job.flow_type == flow_type)

    rows = db.execute(stmt.limit(per).offset((page - 1) * per)).scalars().all()
    items = [
        {
            "id": str(r.id),
            "flow_type": r.flow_type,
            "status": r.status,
            "created_at": r.created_at,
            "finished_at": r.finished_at,
            "counts": {
                "done": r.count_done,
                "failed": r.count_failed,
                "cancelled": r.count_cancelled,
            },
        }
        for r in rows
    ]
    return {"items": items, "page": page, "page_size": per}


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Lightweight meta; UI fetches items separately."""
    row: Job | None = db.get(Job, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="job_not_found")
    return {
        "id": str(row.id),
        "flow_type": row.flow_type,
        "status": row.status,
        "created_at": row.created_at,
        "finished_at": row.finished_at,
        "counts": {
            "done": row.count_done,
            "failed": row.count_failed,
            "cancelled": row.count_cancelled,
        },
    }


@router.get("/{job_id}/items")
def list_job_items(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return items of a job for API consumers (FE table builds on this)."""
    job: Job | None = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")

    rows = (
        db.execute(select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.idx.asc()))
        .scalars()
        .all()
    )

    items = [
        {
            "id": str(r.id),
            "idx": r.idx,
            "status": r.status,
            "retry_count": r.retry_count,
            "error_code": r.error_code,
            "error_message": r.error_message,
            "input": r.input or {},
            "output": r.output or {},
            "timings": r.timings or {},
            "extras": r.extras or {},
            "created_at": r.created_at,
            "finished_at": r.finished_at,
        }
        for r in rows
    ]
    return {"job_id": job_id, "items": items}


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Hard cancel: kill worker process (if any) and cancel pending items."""
    row: Job | None = db.get(Job, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="job_not_found")

    if row.status in (str(JobStatus.DONE), str(JobStatus.FAILED), str(JobStatus.CANCELLED)):
        return {"id": job_id, "status": row.status}

    pid = row.worker_pid
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as exc:
            _logger.warning("job_cancel_kill_failed", job_id=job_id, pid=pid, err=str(exc))

    # Mark unfinished items cancelled.
    db.query(JobItem).filter(JobItem.job_id == job_id, JobItem.finished_at.is_(None)).update(
        {"status": str(ItemStatus.CANCELLED)}, synchronize_session=False
    )

    db.query(Job).filter(Job.id == job_id).update(
        {"status": str(JobStatus.CANCELLED), "worker_pid": None}, synchronize_session=False
    )
    db.commit()

    _logger.info("job_cancelled", job_id=job_id, pid=pid)

    # Free a slot -> schedule next jobs if any.
    schedule_jobs(db)

    return {"id": job_id, "status": str(JobStatus.CANCELLED)}


@router.get("/{job_id}/export.xlsx")
def export_job_excel(job_id: str, db: Session = Depends(get_db)) -> Response:
    """Export one job as an Excel file."""
    try:
        job, content = build_job_excel_from_db(db, job_id)
    except ValueError as exc:
        if str(exc) == "job_not_found":
            raise HTTPException(status_code=404, detail="job_not_found") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = f"job_{job.id}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
