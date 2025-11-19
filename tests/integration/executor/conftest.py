# tests/integration/executor/conftest.py

"""Shared fixtures for executor integration coverage."""
from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, close_all_sessions, sessionmaker
from sqlalchemy.pool import StaticPool

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.db.models import Base, Job, JobItem


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Provide a shared in-memory database for scheduler/worker flows."""

    # WHY: StaticPool + shared cache keeps worker + scheduler views consistent in-memory.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    try:
        yield SessionLocal
    finally:
        close_all_sessions()
        engine.dispose()


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_job() -> Callable[[Session, str, JobStatus, datetime | None], Job]:
    def _create(
        session: Session,
        job_id: str,
        status: JobStatus,
        created_at: datetime | None = None,
        options: dict | None = None,
    ) -> Job:
        job = Job(
            id=job_id,
            flow_type="CRAWL_SIMPLE",
            status=str(status),
            options=options or {},
            count_done=0,
            count_failed=0,
            count_cancelled=0,
            created_at=created_at or datetime.now(UTC),
            finished_at=None,
            worker_pid=None,
        )
        session.add(job)
        session.commit()
        return job

    return _create


@pytest.fixture
def make_item() -> Callable[[Session, str, str, int, ItemStatus], JobItem]:
    def _create(
        session: Session,
        job_id: str,
        item_id: str,
        idx: int,
        status: ItemStatus,
    ) -> JobItem:
        item = JobItem(
            id=item_id,
            job_id=job_id,
            idx=idx,
            status=str(status),
            retry_count=0,
            error_code=None,
            error_message=None,
            input={"idx": idx},
            output=None,
            timings=None,
            extras=None,
            created_at=datetime.now(UTC) - timedelta(minutes=idx),
            finished_at=None,
        )
        session.add(item)
        session.commit()
        return item

    return _create
