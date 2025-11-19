# root/tests/integration/api/conftest.py
"""Fixtures for API integration tests."""
# Why: ensure FastAPI lifespan runs so DB is initialized before requests.

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from engine.core.config.envkeys import DB_URL


@pytest.fixture
def api_client(tmp_path) -> Generator[TestClient, None, None]:
    """Provide TestClient bound to an isolated SQLite DB file."""
    # Set DB URL BEFORE importing app so lifespan uses the right DB.
    db_path = tmp_path / "api.db"
    os.environ[DB_URL] = f"sqlite:///{db_path}"

    mock_static_dir = tmp_path / "static"
    mock_static_dir.mkdir(parents=True, exist_ok=True)

    os.environ["AUTOSUITE_STATIC_DIR"] = str(mock_static_dir)

    # Import after ENV is set to ensure app sees correct settings.
    from service.app.deps import get_session_factory
    from service.app.main import app

    # Use context manager to run startup/shutdown (lifespan).
    with TestClient(app) as client:
        yield client

        # Dispose engine cleanly to avoid SQLite locks on Windows.
        factory = get_session_factory()
        if factory is not None:
            engine = factory().bind
            if engine is not None:
                engine.dispose()
