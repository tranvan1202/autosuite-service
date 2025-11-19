# tests/unit/core/test_errors.py
"""Unit tests for error code mapping."""
# Why: ensure engine surfaces consistent machine-friendly errors.

from __future__ import annotations

import pytest

from engine.core.errors import ErrorCode, to_error_code


@pytest.mark.unit
def test_to_error_code_value_error() -> None:
    """ValueError should map to a stable error code."""
    code = to_error_code(ValueError("bad"))
    assert isinstance(code, ErrorCode)


@pytest.mark.unit
def test_to_error_code_unknown_exception() -> None:
    """Unknown exception should not crash mapping."""
    code = to_error_code(RuntimeError("x"))
    assert isinstance(code, ErrorCode)
