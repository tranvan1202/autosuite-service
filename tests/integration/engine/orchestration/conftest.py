# tests/integration/engine/orchestration/conftest.py
"""Fixtures for JobRunner integration tests."""
from __future__ import annotations

from collections.abc import Callable

import pytest


@pytest.fixture
def configure_runner_settings(monkeypatch: pytest.MonkeyPatch) -> Callable[[int], None]:
    """Patch JobRunner settings for deterministic retries."""

    def _apply(item_max_retries: int) -> None:
        class _Settings:
            def __init__(self, retries: int) -> None:
                self.item_max_retries = retries

        settings = _Settings(item_max_retries)

        def _get_settings() -> _Settings:
            return settings

        monkeypatch.setattr("engine.orchestration.runner.get_settings", _get_settings)

    return _apply
