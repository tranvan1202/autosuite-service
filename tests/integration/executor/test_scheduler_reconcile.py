# tests/integration/executor/test_scheduler_reconcile.py

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.db.models import Job, JobItem
from service.executor import scheduler

pytestmark = pytest.mark.integration


def test_reconcile_marks_orphans_failed(
    db_session: Session,
    make_job,
    make_item,
) -> None:
    job = make_job(
        db_session,
        # WHY: Explicit id makes log assertions easier when reconciling stale rows.
        "job-stale",
        JobStatus.RUNNING,
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.query(Job).filter(Job.id == job.id).update({"worker_pid": 4242})
    db_session.commit()

    make_item(db_session, job.id, "item-1", 0, ItemStatus.PENDING)
    done_item = make_item(db_session, job.id, "item-2", 1, ItemStatus.DONE)
    db_session.query(JobItem).filter(JobItem.id == done_item.id).update(
        {"finished_at": datetime.now(UTC)}
    )
    db_session.commit()

    scheduler.reconcile_stale_jobs(db_session)

    refreshed = db_session.query(Job).filter(Job.id == job.id).one()
    assert refreshed.status == str(JobStatus.FAILED)
    assert refreshed.worker_pid is None

    pending_item = db_session.query(JobItem).filter(JobItem.id == "item-1").one()
    assert pending_item.status == str(ItemStatus.CANCELLED)
    assert pending_item.error_code == "SYSTEM_FAILURE"
    assert pending_item.error_message == "worker process lost before completion"

    completed_item = db_session.query(JobItem).filter(JobItem.id == done_item.id).one()
    assert completed_item.status == str(ItemStatus.DONE)
