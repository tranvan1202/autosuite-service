# root/service/executor/worker.py
"""Standalone job worker subprocess."""
# Why: each process bootstraps DB, runs one job, exits.

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus, JobStatus
from engine.orchestration.runner import run_job
from service.app.deps import get_session_factory, init_db
from service.db.models import Job, JobItem
from service.executor.scheduler import schedule_jobs

_logger = structlog.get_logger(__name__)


def _load_items(db: Session, job_id: str) -> list[dict[str, Any]]:
    """Load enriched items for this job."""
    rows: list[JobItem] = list(
        db.execute(
            select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.idx.asc())
        ).scalars()
    )
    return [cast(dict[str, Any], row.input or {}) for row in rows]


def _persist_results(db: Session, job_id: str, results: list[Any]) -> None:
    """Map ItemResult list back to JobItem + Job summary."""
    # Load object into session:
    rows: list[JobItem] = list(
        db.execute(
            select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.idx.asc())
        ).scalars()
    )

    by_idx: dict[int, JobItem] = {}
    for rec in rows:
        idx_val: int = int(cast(Any, rec).idx)  # avoid Mapped[int] issues
        by_idx[idx_val] = rec

    done = failed = cancelled = 0
    now = datetime.now(UTC)

    for idx, r in enumerate(results):
        item_rec: JobItem | None = by_idx.get(idx)
        if item_rec is None:
            continue

        item_rec.status = str(r.status)
        item_rec.retry_count = int(r.retry_count)
        item_rec.error_code = str(r.error_code) if r.error_code else None
        item_rec.error_message = r.error_message
        item_rec.output = r.output or None
        item_rec.timings = r.timings or None
        item_rec.extras = r.extras or None
        item_rec.finished_at = now

        if r.status == ItemStatus.DONE:
            done += 1
        elif r.status == ItemStatus.FAILED:
            failed += 1
        else:
            cancelled += 1

    # No need for bulk_save_objects: ORM already tracks JobItem instances.
    # db.bulk_save_objects(list(by_idx.values()))

    total = len(results)
    if cancelled > 0 and (done + failed) < total:
        final_status = JobStatus.CANCELLED
    elif failed > 0:
        final_status = JobStatus.FAILED
    else:
        final_status = JobStatus.DONE

    db.query(Job).filter(Job.id == job_id).update(
        {
            "status": str(final_status),
            "finished_at": now,
            "count_done": done,
            "count_failed": failed,
            "count_cancelled": cancelled,
            # clear worker_pid and save to db
            "worker_pid": None,
        },
        synchronize_session=False,
    )
    db.commit()
    _logger.info(
        "worker_job_finished",
        job_id=job_id,
        status=str(final_status),
        done=done,
        failed=failed,
        cancelled=cancelled,
    )


def main() -> None:
    """Read job from DB, run engine, flush results."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    job_id = args.job_id

    # Ensure DB engine/session are initialized in this process.
    asyncio.run(init_db())
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("Session factory not initialized in worker")

    db = factory()
    try:
        row: Job | None = db.query(Job).filter(Job.id == job_id).first()
        if not row:
            _logger.error("worker_job_missing", job_id=job_id)
            return

        db.query(Job).filter(Job.id == job_id).update(
            {"status": str(JobStatus.RUNNING)},
            synchronize_session=False,
        )
        db.commit()

        flow = FlowType(row.flow_type)
        items = _load_items(db, job_id)
        options = dict(row.options or {})
        options["job_id"] = job_id

        results = run_job(flow=flow, items=items, options=options)
        _persist_results(db, job_id, results)
        schedule_jobs(db)
    except Exception as exc:
        _logger.error("worker_job_failed", job_id=job_id, err=str(exc))
        db.query(Job).filter(Job.id == job_id).update(
            {"status": str(JobStatus.FAILED), "worker_pid": None},
            synchronize_session=False,
        )
        db.commit()
        schedule_jobs(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
