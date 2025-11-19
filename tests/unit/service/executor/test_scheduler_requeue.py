# tests/unit/service/executor/test_scheduler_requeue.py

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from engine.core.constants.statuses import JobStatus
from service.executor import scheduler

pytestmark = pytest.mark.unit


def test_schedule_jobs_stops_after_spawn_failure(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    make_job,
) -> None:
    """Scheduler should not loop forever after a spawn failure."""

    class _Settings:
        def __init__(self) -> None:
            self.executor_max_workers = 1

    monkeypatch.setattr(scheduler, "get_settings", lambda: _Settings())

    # WHY: Stable id surfaces clearly in captured scheduler logs during failures.
    job = make_job("job-retry", JobStatus.PENDING)

    spawn_calls: list[str] = []

    def _boom(job_id: str) -> int:
        spawn_calls.append(job_id)
        raise RuntimeError("spawn failed")

    monkeypatch.setattr(scheduler, "_spawn_worker", _boom)

    with pytest.raises(RuntimeError):
        scheduler.schedule_jobs(db_session)

    db_session.refresh(job)
    assert job.status == str(JobStatus.RUNNING)
    assert job.worker_pid is None

    # Second invocation should exit quietly once the RUNNING job is counted.
    scheduler.schedule_jobs(db_session)
    assert spawn_calls == ["job-retry"]
