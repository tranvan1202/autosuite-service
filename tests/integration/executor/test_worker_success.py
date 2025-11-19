# tests/integration/executor/test_worker_success.py

from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import Any

import pytest

from engine.core.constants.statuses import ItemStatus, JobStatus
from engine.core.models.item_result import ItemResult
from service.db.models import Job, JobItem
from service.executor import worker

pytestmark = pytest.mark.integration


def _make_result(status: ItemStatus, output: dict[str, Any] | None = None) -> ItemResult:
    return ItemResult(
        status=status,
        retry_count=0,
        error_code=None,
        output=output,
        timings={"duration": 0.4},
        extras={"source": "runner"},
    )


def test_worker_main_persists_success(
    session_factory,
    make_job,
    make_item,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = session_factory()
    # WHY: Reuse readable job id for downstream assertions and CLI args.
    job = make_job(session, "job-success", JobStatus.PENDING, created_at=datetime.now(UTC))
    make_item(session, job.id, "item-1", 0, ItemStatus.PENDING)
    make_item(session, job.id, "item-2", 1, ItemStatus.PENDING)
    session.close()

    schedule_calls: list[Any] = []

    async def _init_db_stub() -> None:
        return None

    def _get_factory():
        return session_factory

    def _run_job(flow, items, options):  # noqa: ANN001 - signature mirrors real function
        # WHY: Exercise happy-path persistence with multiple DONE results.
        return [
            _make_result(ItemStatus.DONE, {"idx": 0}),
            _make_result(ItemStatus.DONE, {"idx": 1}),
        ]

    def _schedule(db):
        schedule_calls.append(db.query(Job).count())

    monkeypatch.setattr(worker, "init_db", _init_db_stub)
    monkeypatch.setattr(worker, "get_session_factory", _get_factory)
    monkeypatch.setattr(worker, "run_job", _run_job)
    monkeypatch.setattr(worker, "schedule_jobs", _schedule)

    monkeypatch.setenv("PYTHONPATH", "")
    monkeypatch.setattr(sys, "argv", ["worker", "--job-id", "job-success"])

    worker.main()

    check_session = session_factory()
    row = check_session.query(Job).filter(Job.id == "job-success").one()
    assert row.status == str(JobStatus.DONE)
    assert row.count_done == 2
    assert row.count_failed == 0
    assert row.worker_pid is None

    items = (
        check_session.query(JobItem)
        .filter(JobItem.job_id == "job-success")
        .order_by(JobItem.idx.asc())
        .all()
    )
    assert [item.status for item in items] == [str(ItemStatus.DONE), str(ItemStatus.DONE)]
    assert items[0].output == {"idx": 0}
    assert items[1].output == {"idx": 1}
    assert len(schedule_calls) == 1  # worker should trigger scheduler tick
    check_session.close()
