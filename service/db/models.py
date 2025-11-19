# root/service/db/models.py
"""ORM models: jobs and items (generic columns, not *_json)."""
# Why: keep schema stable while payloads evolve.

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .types import JSONFlex


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flow_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    options: Mapped[dict | None] = mapped_column(JSONFlex, nullable=True)

    count_done: Mapped[int] = mapped_column(Integer, default=0)
    count_failed: Mapped[int] = mapped_column(Integer, default=0)
    count_cancelled: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    worker_pid = mapped_column(Integer, nullable=True)


class JobItem(Base):
    __tablename__ = "job_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(
        String, ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    idx: Mapped[int] = mapped_column(Integer, index=True)

    status: Mapped[str] = mapped_column(String, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    input: Mapped[dict | None] = mapped_column(JSONFlex, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONFlex, nullable=True)
    timings: Mapped[dict | None] = mapped_column(JSONFlex, nullable=True)

    extras: Mapped[dict | None] = mapped_column(JSONFlex, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
