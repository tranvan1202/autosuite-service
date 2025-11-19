# tests/integration/service/executor/scheduler/test_single_job_basic.py
"""Scheduler: single pending job, single worker slot."""
# Why: sanity check core path before race/edge scenarios.

from __future__ import annotations

import pytest

from engine.core.constants.statuses import JobStatus
from service.executor.scheduler import schedule_jobs


@pytest.mark.integration
def test_single_pending_job_gets_scheduled(
    db_session,
    max_workers_1,
    spawn_log,
    make_job,
) -> None:
    job = make_job("job-1", JobStatus.PENDING)

    schedule_jobs(db_session)
    db_session.refresh(job)

    assert job.status == str(JobStatus.RUNNING)
    assert job.worker_pid is not None
    assert len(spawn_log) == 1
    assert spawn_log[0][0] == "job-1"
    assert spawn_log[0][1] == job.worker_pid
