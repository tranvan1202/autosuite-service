# root/engine/core/errors.py
"""Unified error taxonomy + exception classes + mappers."""
# Why: one home for ErrorCode avoids enum/typing conflicts across modules.

from __future__ import annotations

from enum import Enum, StrEnum, unique
from typing import Any

import structlog

_logger = structlog.get_logger(__name__)


@unique
class ErrorCode(StrEnum):
    """Machine-stable error taxonomy for flows and orchestration."""

    NONE = "NONE"
    NAVIGATION_ERROR = "NAVIGATION_ERROR"
    TIMEOUT = "TIMEOUT"
    INVALID_INPUT = "INVALID_INPUT"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    UNKNOWN = "UNKNOWN"
    DEDUPED = "DEDUPED"


# ---- Exception classes with typed `.code` for mypy ----
class NonRetryableError(Exception):
    """Permanent failure; retrying wastes resources."""

    code: ErrorCode = ErrorCode.INVALID_INPUT


class RetryableError(Exception):
    """Transient failure; eligible for limited retries."""

    code: ErrorCode = ErrorCode.TIMEOUT


class InputInvalidError(NonRetryableError):
    """User input fails validation."""

    code: ErrorCode = ErrorCode.INVALID_INPUT


class DedupeError(NonRetryableError):
    """Duplicate work detected and skipped."""

    code: ErrorCode = ErrorCode.DEDUPED


class NavigationError(RetryableError):
    """Navigation/network hiccup likely to pass on retry."""

    code: ErrorCode = ErrorCode.NAVIGATION_ERROR


class FlowTimeoutError(RetryableError):
    """Timed out waiting for a page/resource."""

    code: ErrorCode = ErrorCode.TIMEOUT


# ---- Mapping helpers (safe for mypy) ----
def coerce_error_code(value: Any) -> ErrorCode:
    """Map unknown enum/strings to ErrorCode, else UNKNOWN."""
    if isinstance(value, ErrorCode):
        return value

    if isinstance(value, Enum):
        enum_val = getattr(value, "value", None)
        if isinstance(enum_val, str):
            try:
                return ErrorCode(enum_val)
            except ValueError:
                pass
        member = ErrorCode.__members__.get(value.name)
        if isinstance(member, ErrorCode):
            return member
        return ErrorCode.UNKNOWN

    if isinstance(value, str):
        # Try by value
        try:
            return ErrorCode(value)
        except ValueError:
            # Try by name
            member = ErrorCode.__members__.get(value)
            if isinstance(member, ErrorCode):
                return member
        return ErrorCode.UNKNOWN

    return ErrorCode.UNKNOWN


def to_error_code(exc: Exception) -> ErrorCode:
    """Best-effort mapping from arbitrary exception → ErrorCode."""
    code_attr = getattr(exc, "code", None)
    mapped = coerce_error_code(code_attr)
    if mapped is ErrorCode.UNKNOWN:
        _logger.debug("map_exc_to_error_code", exc_type=type(exc).__name__)
    return mapped
