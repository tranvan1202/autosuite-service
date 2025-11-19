# tests/unit/service/executor/conftest.py

"""Fixtures for scheduler/worker unit tests."""
from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.db.models import Base, Job, JobItem


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide isolated in-memory DB session for unit tests."""

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def make_job(db_session: Session) -> Callable[[str, JobStatus], Job]:
    """Create a persisted Job row."""

    def _create(job_id: str, status: JobStatus) -> Job:
        job = Job(
            id=job_id,
            flow_type="CRAWL_SIMPLE",
            status=str(status),
            options=None,
            count_done=0,
            count_failed=0,
            count_cancelled=0,
            created_at=datetime.now(UTC),
            finished_at=None,
            worker_pid=None,
        )
        db_session.add(job)
        db_session.commit()
        return job

    return _create


@pytest.fixture
def make_item(db_session: Session) -> Callable[[str, str, int, ItemStatus], JobItem]:
    """Create a persisted JobItem row."""

    def _create(job_id: str, item_id: str, idx: int, status: ItemStatus) -> JobItem:
        item = JobItem(
            id=item_id,
            job_id=job_id,
            idx=idx,
            status=str(status),
            retry_count=0,
            error_code=None,
            error_message=None,
            input={},
            output=None,
            timings=None,
            extras=None,
            created_at=datetime.now(UTC),
            finished_at=None,
        )
        db_session.add(item)
        db_session.commit()
        return item

    return _create
