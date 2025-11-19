# tests/unit/service/executor/test_worker_persist.py

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from engine.core.constants.statuses import ItemStatus, JobStatus
from engine.core.errors import ErrorCode
from engine.core.models.item_result import ItemResult
from service.db.models import Job, JobItem
from service.executor.worker import _persist_results

pytestmark = pytest.mark.unit


def test_persist_results_applies_cancelled_priority(
    db_session: Session, make_job, make_item
) -> None:
    make_job("job-1", JobStatus.RUNNING)
    make_item("job-1", "item-1", 0, ItemStatus.PENDING)
    make_item("job-1", "item-2", 1, ItemStatus.PENDING)

    # WHY: Simulate dedupe cancellation overriding successful item to check summary rollup.
    results = [
        ItemResult(
            status=ItemStatus.DONE,
            retry_count=0,
            error_code=ErrorCode.NONE,
            output={"value": 1},
        ),
        ItemResult(
            status=ItemStatus.CANCELLED,
            retry_count=0,
            error_code=ErrorCode.DEDUPED,
            error_message="skip",
        ),
    ]

    _persist_results(db_session, "job-1", results)

    job = db_session.query(Job).filter(Job.id == "job-1").one()
    assert job.status == str(JobStatus.CANCELLED)
    assert job.count_done == 1
    assert job.count_cancelled == 1
    assert job.count_failed == 0
    assert job.finished_at is not None
    assert job.worker_pid is None

    item_done = db_session.query(JobItem).filter(JobItem.id == "item-1").one()
    assert item_done.status == str(ItemStatus.DONE)
    assert item_done.output == {"value": 1}
    assert item_done.finished_at is not None

    item_cancelled = db_session.query(JobItem).filter(JobItem.id == "item-2").one()
    assert item_cancelled.status == str(ItemStatus.CANCELLED)
    assert item_cancelled.error_code == ErrorCode.DEDUPED
    assert item_cancelled.error_message == "skip"
