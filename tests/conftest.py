# root/tests/conftest.py

"""Global pytest hooks for reporting/logging."""
# Why: keep reports CI-friendly without polluting test code.

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from engine.core.config.envkeys import (
    ARTIFACTS_DIR,
    EXECUTOR_MAX_WORKERS,
    PW_HEADLESS,
    PW_TRACING,
    REPORTS_DIR,
    UI_POLL_MS,
)
from service.constants.api import API_V1_PREFIX

# Infer project root = parent of tests/
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def api_base() -> str:
    return API_V1_PREFIX


def _repo_root() -> Path:
    # File này nằm ở <repo>/tests/conftest.py → parent chính là repo root
    return Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def fresh_settings_each_test(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Ensure Settings snapshot is fresh for each test (no bleed)."""
    # Default off before each test
    monkeypatch.setenv(PW_TRACING, "off")
    from service.app.deps import reset_settings_cache

    reset_settings_cache()
    try:
        yield
    finally:
        # Clear again
        reset_settings_cache()


@pytest.fixture(scope="session", autouse=True)
def test_env() -> None:
    root = _repo_root()
    var = root / "var"
    (var / "artifacts").mkdir(parents=True, exist_ok=True)
    (var / "reports").mkdir(parents=True, exist_ok=True)
    (var / "test_dbs").mkdir(parents=True, exist_ok=True)

    os.environ.setdefault(ARTIFACTS_DIR, str(var / "artifacts"))
    os.environ.setdefault(REPORTS_DIR, str(var / "reports"))
    os.environ.setdefault(UI_POLL_MS, "500")
    os.environ.setdefault(EXECUTOR_MAX_WORKERS, "1")
    os.environ.setdefault(PW_HEADLESS, "1")
    os.environ.setdefault(PW_TRACING, "off")


@pytest.fixture
def test_db_url(request: pytest.FixtureRequest) -> str:
    root = _repo_root()
    dbfile = root / "var" / "test_dbs" / "app_stg.db"
    return f"sqlite:///{dbfile}"
