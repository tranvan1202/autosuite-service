# tests/integration/executor/test_scheduler_capacity.py

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from engine.core.constants.statuses import JobStatus
from service.db.models import Job
from service.executor import scheduler

pytestmark = pytest.mark.integration


def test_scheduler_respects_capacity(
    db_session: Session,
    make_job,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Settings:
        def __init__(self) -> None:
            self.executor_max_workers = 2

    monkeypatch.setattr(scheduler, "get_settings", lambda: _Settings())

    start = datetime.now(UTC) - timedelta(minutes=5)
    jobs = [
        # WHY: Sequential timestamps ensure FIFO ordering is deterministic.
        make_job(
            db_session, f"job-{idx}", JobStatus.PENDING, created_at=start + timedelta(minutes=idx)
        )
        for idx in range(3)
    ]

    spawn_log: list[str] = []

    def _spawn(job_id: str) -> int:
        spawn_log.append(job_id)
        return 1000 + len(spawn_log)

    monkeypatch.setattr(scheduler, "_spawn_worker", _spawn)

    scheduler.schedule_jobs(db_session)
    db_session.expire_all()

    refreshed = db_session.query(Job).order_by(Job.id.asc()).all()
    running = [row for row in refreshed if row.status == str(JobStatus.RUNNING)]

    assert len(spawn_log) == 2
    assert {row.id for row in running} == {jobs[0].id, jobs[1].id}
    assert all(row.worker_pid is not None for row in running)
    tail_job = db_session.query(Job).filter(Job.id == jobs[2].id).one()
    assert tail_job.status == str(JobStatus.PENDING)
