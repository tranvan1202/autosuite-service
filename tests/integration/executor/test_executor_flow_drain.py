# tests/integration/executor/test_executor_flow_drain.py

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from engine.core.constants.statuses import ItemStatus, JobStatus
from engine.core.models.item_result import ItemResult
from service.db.models import Job, JobItem
from service.executor import scheduler, worker

pytestmark = pytest.mark.integration


def _item_result(status: ItemStatus, extras: dict | None = None) -> ItemResult:
    return ItemResult(
        status=status,
        retry_count=0,
        error_code=None,
        output={"status": str(status)},
        timings={"duration": 0.2},
        extras=extras or {},
    )


def test_scheduler_worker_drain_queue(
    db_session: Session,
    make_job,
    make_item,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Settings:
        def __init__(self) -> None:
            self.executor_max_workers = 1

    monkeypatch.setattr(scheduler, "get_settings", lambda: _Settings())

    # Seed two jobs with single items to simulate queue backlog.
    # WHY: Sequential ids mirror backlog ordering across scheduler + worker assertions.
    job1 = make_job(db_session, "job-drain-1", JobStatus.PENDING, created_at=datetime.now(UTC))
    job2 = make_job(db_session, "job-drain-2", JobStatus.PENDING, created_at=datetime.now(UTC))
    make_item(db_session, job1.id, "item-a", 0, ItemStatus.PENDING)
    make_item(db_session, job2.id, "item-b", 0, ItemStatus.PENDING)

    spawn_log: list[str] = []

    def _spawn(job_id: str) -> int:
        spawn_log.append(job_id)
        return 2000 + len(spawn_log)

    monkeypatch.setattr(scheduler, "_spawn_worker", _spawn)

    scheduler.schedule_jobs(db_session)
    db_session.expire_all()

    first_job = db_session.query(Job).filter(Job.id == job1.id).one()
    assert first_job.status == str(JobStatus.RUNNING)

    worker._persist_results(
        db_session,
        job1.id,
        [_item_result(ItemStatus.DONE)],
    )
    db_session.expire_all()

    scheduler.schedule_jobs(db_session)
    db_session.expire_all()

    second_job = db_session.query(Job).filter(Job.id == job2.id).one()
    assert second_job.status == str(JobStatus.RUNNING)

    worker._persist_results(
        db_session,
        job2.id,
        [_item_result(ItemStatus.DONE)],
    )
    db_session.expire_all()

    final_jobs = db_session.query(Job).order_by(Job.id.asc()).all()
    assert all(row.status == str(JobStatus.DONE) for row in final_jobs)
    assert all(row.worker_pid is None for row in final_jobs)
    assert spawn_log == [job1.id, job2.id]

    items = db_session.query(JobItem).order_by(JobItem.job_id.asc()).all()
    assert all(item.status == str(ItemStatus.DONE) for item in items)
