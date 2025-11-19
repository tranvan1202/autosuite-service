from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import Any

import pytest

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.db.models import Job
from service.executor import worker

pytestmark = pytest.mark.integration


def test_worker_main_handles_run_job_failure(
    session_factory,
    make_job,
    make_item,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = session_factory()
    # WHY: Readable job id surfaces quickly in scheduler + worker logs.
    job = make_job(session, "job-fail", JobStatus.PENDING, created_at=datetime.now(UTC))
    make_item(session, job.id, "item-err", 0, ItemStatus.PENDING)
    session.close()

    schedule_calls: list[Any] = []

    async def _init_db_stub() -> None:
        return None

    def _get_factory():
        return session_factory

    def _schedule(db):
        schedule_calls.append(db.query(Job).count())

    def _run_job(*_) -> None:
        # WHY: Force worker into failure branch to assert retry + cleanup behaviour.
        raise RuntimeError("engine down")

    monkeypatch.setattr(worker, "init_db", _init_db_stub)
    monkeypatch.setattr(worker, "get_session_factory", _get_factory)
    monkeypatch.setattr(worker, "run_job", _run_job)
    monkeypatch.setattr(worker, "schedule_jobs", _schedule)
    monkeypatch.setattr(sys, "argv", ["worker", "--job-id", "job-fail"])

    worker.main()

    check_session = session_factory()
    row = check_session.query(Job).filter(Job.id == "job-fail").one()
    assert row.status == str(JobStatus.FAILED)
    assert row.worker_pid is None
    assert len(schedule_calls) == 1
    check_session.close()
