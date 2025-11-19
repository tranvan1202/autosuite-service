# tests/unit/service/executor/test_scheduler_metrics.py

from __future__ import annotations

import pytest

from engine.core.constants.statuses import JobStatus
from service.executor.scheduler import _running_jobs_count

pytestmark = pytest.mark.unit


def test_running_jobs_count_matches_active_jobs(db_session, make_job) -> None:
    make_job("job-1", JobStatus.RUNNING)
    make_job("job-2", JobStatus.RUNNING)
    make_job("job-3", JobStatus.PENDING)

    assert _running_jobs_count(db_session) == 2
