# tests/integration/service/executor/scheduler/test_reconcile_stale_jobs.py
"""Scheduler: reconcile orphan RUNNING jobs and continue queue."""
# Why: restart-safe behavior for crashed workers.

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.db.models import Job, JobItem
from service.executor.scheduler import reconcile_stale_jobs, schedule_jobs


@pytest.mark.integration
def test_reconcile_stale_running_job_and_schedule_next(
    db_session,
    max_workers_1,
    spawn_log,
) -> None:
    """Stale RUNNING job becomes FAILED and next PENDING is scheduled."""
    now = datetime.now(UTC)
    stale = Job(
        id="job-stale",
        flow_type="CRAWL_SIMPLE",
        status=str(JobStatus.RUNNING),
        options=None,
        count_done=0,
        count_failed=0,
        count_cancelled=0,
        created_at=now,
        finished_at=None,
        worker_pid=9999,
    )

    pending = Job(
        id="job-next",
        flow_type="CRAWL_SIMPLE",
        status=str(JobStatus.PENDING),
        options=None,
        count_done=0,
        count_failed=0,
        count_cancelled=0,
        created_at=now,
        finished_at=None,
        worker_pid=None,
    )

    item = JobItem(
        id="item-1",
        job_id="job-stale",
        idx=0,
        status=str(ItemStatus.PENDING),
        retry_count=0,
        error_code=None,
        error_message=None,
        input={},
        output=None,
        timings=None,
        extras=None,
        created_at=now,
        finished_at=None,
    )
    db_session.add_all([stale, pending, item])
    db_session.commit()

    reconcile_stale_jobs(db_session)
    schedule_jobs(db_session)
    db_session.refresh(stale)
    db_session.refresh(pending)
    db_session.refresh(item)

    assert stale.status == str(JobStatus.FAILED)
    assert stale.worker_pid is None
    assert item.status == str(ItemStatus.CANCELLED)
    assert pending.status == str(JobStatus.RUNNING)
    assert pending.worker_pid is not None
    assert len(spawn_log) == 1
    assert spawn_log[0][0] == "job-next"
