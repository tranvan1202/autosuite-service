# root/tests/e2e/system/conftest.py
"""Fixtures for system E2E tests (API -> engine -> DB)."""
# Why: run real app with inline worker instead of subprocess for determinism.

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from engine.core.config.envkeys import DB_URL, EXECUTOR_MAX_WORKERS
from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus, JobStatus
from engine.orchestration.runner import run_job


@pytest.fixture
def system_client(
    test_db_url: str, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    """Run real app with inline worker, artifacts under ./var."""
    # Pin DB for this test
    monkeypatch.setenv(DB_URL, test_db_url)
    # Ensure single worker
    monkeypatch.setenv(EXECUTOR_MAX_WORKERS, "1")

    # Import AFTER env is set
    from datetime import datetime

    from service.app.deps import get_session_factory
    from service.app.main import app
    from service.db.models import Job, JobItem
    from service.executor import scheduler as sched

    # Use context manager so FastAPI lifespan runs -> init_db() executed.
    with TestClient(app) as client:
        factory = get_session_factory()
        assert factory is not None
        db = factory()

        def _inline_spawn(job_id: str) -> int:
            """Execute the job synchronously instead of spawning subprocess."""
            job_row: Job | None = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
            if job_row is None:
                return 0

            rows = list(
                db.execute(
                    select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.idx.asc())
                ).scalars()
            )
            items: list[dict[str, Any]] = [(r.input or {}) for r in rows]

            flow = FlowType(job_row.flow_type)
            options = dict(job_row.options or {})
            options["job_id"] = job_id

            results = run_job(flow=flow, items=items, options=options)

            done = failed = cancelled = 0
            for idx, res in enumerate(results):
                rec = rows[idx]
                rec.status = str(res.status)
                rec.retry_count = res.retry_count
                rec.error_code = str(res.error_code) if res.error_code else None
                rec.error_message = res.error_message
                rec.output = res.output or None
                rec.timings = res.timings or None
                rec.extras = res.extras or None
                rec.finished_at = datetime.now(UTC)
                if res.status.name == ItemStatus.DONE:
                    done += 1
                elif res.status.name == ItemStatus.FAILED:
                    failed += 1
                else:
                    cancelled += 1

            job_row.status = JobStatus.DONE if failed == 0 else JobStatus.FAILED
            job_row.count_done = done
            job_row.count_failed = failed
            job_row.count_cancelled = cancelled
            job_row.finished_at = datetime.now(UTC)

            db.commit()
            return 1000  # fake pid

        # Inline worker to keep test fast/deterministic
        monkeypatch.setattr(sched, "_spawn_worker", _inline_spawn)

        try:
            yield client
        finally:
            db.close()
            engine = factory().bind
            if engine is not None:
                engine.dispose()
