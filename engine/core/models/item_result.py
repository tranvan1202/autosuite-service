# root/engine/core/models/item_result.py
"""Per-item result used by runner → service → UI."""
# Why: a single DTO keeps serialization, masking, and tests consistent.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.errors import ErrorCode
from ..constants.statuses import ItemStatus


@dataclass(slots=True)
class ItemResult:
    """Flattened outcome for one item; easy to render or export."""

    status: ItemStatus
    retry_count: int = 0
    error_code: ErrorCode = ErrorCode.NONE
    error_message: str | None = None
    output: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    timings: dict[str, float] = field(default_factory=dict)
