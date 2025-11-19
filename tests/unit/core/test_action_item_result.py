# tests/unit/core/test_action_item_result.py
"""Unit tests for ActionResult and ItemResult contracts."""
# Why: downstream logic assumes these fields exist.

from __future__ import annotations

import pytest

from engine.core.constants.statuses import ItemStatus
from engine.core.errors import ErrorCode
from engine.core.models.action_result import ActionResult
from engine.core.models.item_result import ItemResult


@pytest.mark.unit
def test_action_result_success() -> None:
    """ok ActionResult should carry value and no error."""
    ar = ActionResult(ok=True, value={"x": 1})
    assert ar.ok is True
    assert ar.value == {"x": 1}
    assert ar.error_code == ErrorCode.NONE


@pytest.mark.unit
def test_item_result_failed() -> None:
    """FAILED ItemResult should expose error metadata."""
    ir = ItemResult(
        status=ItemStatus.FAILED,
        error_code=ErrorCode.UNKNOWN,
        error_message="boom",
    )
    assert ir.status == ItemStatus.FAILED
    assert ir.error_code == ErrorCode.UNKNOWN
    assert ir.error_message == "boom"
