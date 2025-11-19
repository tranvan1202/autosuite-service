# root/engine/orchestration/events.py
"""Lightweight job/item events for logs and metrics."""
# Why: explicit event shapes make telemetry and hooks predictable.

from __future__ import annotations

from dataclasses import dataclass

from ..core.constants.flows import FlowType
from ..core.constants.statuses import ItemStatus, JobStatus


@dataclass(slots=True)
class JobStarted:
    """Emitted once per job start."""

    job_id: str
    flow: FlowType


@dataclass(slots=True)
class JobFinished:
    """Emitted once per job end."""

    job_id: str
    flow: FlowType
    status: JobStatus


@dataclass(slots=True)
class ItemStarted:
    """Emitted before each item run."""

    job_id: str
    item_index: int


@dataclass(slots=True)
class ItemFinished:
    """Emitted after each item run."""

    job_id: str
    item_index: int
    status: ItemStatus
