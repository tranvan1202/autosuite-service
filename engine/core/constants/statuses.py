# root/engine/core/constants/statuses.py
"""Stable statuses for jobs and items."""
# Why: UI/API/tests can rely on a single vocabulary.

from __future__ import annotations

from enum import StrEnum, unique


@unique
class JobStatus(StrEnum):
    """High-level job lifecycle."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ItemStatus(StrEnum):
    """Per-item lifecycle; mirrors JobStatus."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SYSTEM_FAILURE = "SYSTEM_FAILURE"
