# tests/unit/context/conftest.py

"""Fixtures for Playwright session unit tests."""
# WHY: Local fixtures keep Playwright-heavy stubs scoped to context tests only.

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def secrets_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "secrets"
    (root / "cookies").mkdir(parents=True)
    (root / "form_auth").mkdir(parents=True)
    monkeypatch.setattr("engine.automation.playwright.session.injectors._SECRETS_ROOT", root)
    return root
