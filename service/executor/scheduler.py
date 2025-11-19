# root/service/app/scheduler.py
"""Minimal FIFO scheduler for worker subprocesses."""
# Why: enforce AUTOSUITE_EXECUTOR_MAX_WORKERS with simple DB-based queue.

from __future__ import annotations

import subprocess
import sys

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.app.deps import get_settings
from service.db.models import Job, JobItem

_logger = structlog.get_logger(__name__)


def _running_jobs_count(db: Session) -> int:
    """Count jobs currently marked RUNNING."""
    val: int | None = db.scalar(
        select(func.count()).select_from(Job).where(Job.status == str(JobStatus.RUNNING))
    )
    return int(val or 0)


def _spawn_worker(job_id: str) -> int:
    """Start worker subprocess for a job and return its PID."""
    cmd = [
        sys.executable,
        "-m",
        "service.executor.worker",
        "--job-id",
        job_id,
    ]
    # Why: detached enough for Render/local; we only care about pid.
    proc = subprocess.Popen(cmd, close_fds=True)  # noqa: S603 - fixed, trusted args
    return int(proc.pid)


def reconcile_stale_jobs(db: Session) -> None:
    """Mark orphan RUNNING jobs as failed so queue can move on.
    Why: In our model, a process restart kills workers. Any RUNNING here is orphaned.
    """

    stale_rows = db.execute(select(Job).where(Job.status == str(JobStatus.RUNNING))).scalars().all()

    stale: list[Job] = list(stale_rows)

    if not stale:
        return

    for job in stale:
        # Mark unfinished items as cancelled due to system failure.
        db.query(JobItem).filter(
            JobItem.job_id == job.id,
            JobItem.finished_at.is_(None),
        ).update(
            {
                "status": str(ItemStatus.CANCELLED),
                "error_code": "SYSTEM_FAILURE",
                "error_message": "worker process lost before completion",
            },
            synchronize_session=False,
        )

        job.status = str(JobStatus.FAILED)
        job.worker_pid = None

        _logger.warning("reconciled_stale_job", job_id=job.id)

    db.commit()


def schedule_jobs(db: Session) -> None:
    """Fill available slots with oldest PENDING jobs in a race-safe way.

    Pattern: pick candidate id -> atomic UPDATE where still PENDING -> if 1 row affected, spawn worker.
    This avoids two schedulers claiming the same job.
    """
    s = get_settings()
    max_workers = max(int(s.executor_max_workers), 1)

    while True:
        running = _running_jobs_count(db)
        if running >= max_workers:
            return

        slots = max_workers - running
        if slots <= 0:
            return

        claimed_any = False

        for _ in range(slots):
            # Oldest PENDING first (FIFO) job id only.
            candidate_id: str | None = db.scalar(
                select(Job.id)
                .where(
                    Job.status == str(JobStatus.PENDING),
                    Job.worker_pid.is_(None),
                )
                .order_by(Job.created_at.asc())
                .limit(1)
            )
            if candidate_id is None:
                # No more pending jobs.
                break

            # Atomic claim: only flip to RUNNING if still PENDING and no pid.
            updated = (
                db.query(Job)
                .filter(
                    Job.id == candidate_id,
                    Job.status == str(JobStatus.PENDING),
                    Job.worker_pid.is_(None),
                )
                .update(
                    {"status": str(JobStatus.RUNNING)},
                    synchronize_session=False,
                )
            )
            if updated != 1:
                # Someone else claimed concurrently; retry with next slot.
                db.rollback()
                continue

            db.commit()  # persist RUNNING state before spawning

            # Now we are the owner for this job id.
            pid = _spawn_worker(str(candidate_id))

            db.query(Job).filter(Job.id == candidate_id).update(
                {"worker_pid": pid},
                synchronize_session=False,
            )
            db.commit()

            _logger.info("scheduler_started_job", job_id=str(candidate_id), pid=pid)
            claimed_any = True

        # If in this loop iteration we couldn't claim anything, stop to avoid tight spin.
        if not claimed_any:
            return
