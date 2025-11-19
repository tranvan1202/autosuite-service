# tests/integration/service/executor/scheduler/conftest.py
"""Shared fixtures for scheduler integration tests."""
# Why: isolate DB per test and fake worker spawn behavior.

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from engine.core.constants.statuses import ItemStatus, JobStatus
from service.db.models import Base, Job, JobItem


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide isolated in-memory DB session per test."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


class _DummySettings:
    """Minimal settings stub for scheduler tests."""

    executor_max_workers: int = 1


@pytest.fixture
def max_workers_1(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force scheduler to use a single worker slot."""

    def _get_settings_stub() -> _DummySettings:
        return _DummySettings()

    monkeypatch.setattr("service.executor.scheduler.get_settings", _get_settings_stub)


@pytest.fixture
def max_workers_2(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force scheduler to allow two concurrent workers."""

    class _Two:
        executor_max_workers = 2

    def _get_settings_stub() -> Any:
        return _Two()

    monkeypatch.setattr("service.executor.scheduler.get_settings", _get_settings_stub)


@pytest.fixture
def spawn_log(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    """Capture spawned workers instead of launching real subprocesses."""
    log: list[tuple[str, int]] = []

    def _fake_spawn(job_id: str) -> int:
        pid = 1000 + len(log)
        log.append((job_id, pid))
        return pid

    monkeypatch.setattr("service.executor.scheduler._spawn_worker", _fake_spawn)
    return log


@pytest.fixture
def make_job(db_session: Session):
    """Factory to create minimal valid Job rows."""

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
def make_item(db_session: Session):
    """Factory to create minimal valid JobItem rows."""

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
