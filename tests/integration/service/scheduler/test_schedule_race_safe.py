# tests/integration/service/executor/scheduler/test_schedule_race_safe.py
"""Scheduler: avoid double-claiming a single job."""
# Why: prove optimistic claim logic is race-safe for one job.

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.core.constants.statuses import JobStatus
from service.db.models import Base, Job
from service.executor.scheduler import schedule_jobs


@pytest.mark.integration
def test_two_schedulers_cannot_claim_same_job(spawn_log, max_workers_1) -> None:
    """Two schedule_jobs calls against same DB should spawn one worker."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    db1 = SessionLocal()
    db2 = SessionLocal()

    job = Job(
        id="job-race",
        flow_type="CRAWL_SIMPLE",
        status=str(JobStatus.PENDING),
        options=None,
        count_done=0,
        count_failed=0,
        count_cancelled=0,
        created_at=datetime.now(UTC),
        finished_at=None,
        worker_pid=None,
    )
    db1.add(job)
    db1.commit()

    schedule_jobs(db1)
    db1.commit()

    schedule_jobs(db2)
    db2.commit()

    db_final = SessionLocal()
    job_row = db_final.query(Job).filter(Job.id == "job-race").first()

    assert job_row is not None
    assert job_row.status == str(JobStatus.RUNNING)
    assert job_row.worker_pid is not None
    assert len(spawn_log) == 1
    assert spawn_log[0][0] == "job-race"

    db1.close()
    db2.close()
    db_final.close()
    engine.dispose()
