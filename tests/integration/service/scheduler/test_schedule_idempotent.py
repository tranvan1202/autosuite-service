# tests/integration/service/executor/scheduler/test_schedule_idempotent.py
"""Scheduler: repeated calls must not spawn duplicate workers."""
# Why: defensive against noisy callers.

from __future__ import annotations

import pytest

from engine.core.constants.statuses import JobStatus
from service.executor.scheduler import schedule_jobs


@pytest.mark.integration
def test_schedule_jobs_is_idempotent_for_claimed_job(
    db_session,
    max_workers_1,
    spawn_log,
    make_job,
) -> None:
    job = make_job("job-1", JobStatus.PENDING)

    schedule_jobs(db_session)
    db_session.refresh(job)
    first_pid = job.worker_pid

    schedule_jobs(db_session)
    db_session.refresh(job)

    assert job.status == str(JobStatus.RUNNING)
    assert job.worker_pid == first_pid
    assert len(spawn_log) == 1
