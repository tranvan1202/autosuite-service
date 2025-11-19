# root/engine/core/models/action_result.py
"""Action-level result wrapper used across flows and orchestration."""
# Why: one shape for success/failure simplifies retries, metrics, and tests.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from ...core.errors import ErrorCode

T = TypeVar("T")


@dataclass(slots=True)
class ActionResult(Generic[T]):
    """Capture value or error with context for observability."""

    ok: bool
    value: T | None = None
    error_code: ErrorCode = ErrorCode.NONE
    error_message: str | None = None
    retry_count: int = 0
    timings: dict[str, float] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
