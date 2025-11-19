# tests/unit/engine/orchestration/conftest.py
"""Fixtures for JobRunner unit tests."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from engine.core.errors import ErrorCode


@dataclass
class StubActionResult:
    """Lightweight stand-in for flow adapter results."""

    ok: bool
    value: Any = None
    error_code: ErrorCode = ErrorCode.UNKNOWN
    error_message: str | None = None
    timings: dict[str, float] | None = None
    extras: dict[str, Any] | None = None


@pytest.fixture
def make_action_result() -> Callable[..., StubActionResult]:
    """Factory for StubActionResult instances."""

    def _create(**kwargs: Any) -> StubActionResult:
        return StubActionResult(**kwargs)

    return _create


@pytest.fixture
def configure_runner_settings(monkeypatch: pytest.MonkeyPatch) -> Callable[[int], None]:
    """Override `get_settings` so tests can tweak retry counts."""

    def _apply(item_max_retries: int) -> None:
        class _Settings:
            def __init__(self, retries: int) -> None:
                self.item_max_retries = retries

        settings = _Settings(item_max_retries)

        def _get_settings() -> _Settings:
            return settings

        monkeypatch.setattr("engine.orchestration.runner.get_settings", _get_settings)

    return _apply
