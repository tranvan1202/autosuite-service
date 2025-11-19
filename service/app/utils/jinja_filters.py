# root/service/app/utils/jinja_filters.py
"""Jinja filters for compact rendering."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import structlog

_logger = structlog.get_logger(__name__)

DEFAULT_TZ = "Asia/Ho_Chi_Minh"
UTC = ZoneInfo("UTC")


def short_text(v: Any, maxlen: int = 120) -> str:
    """Return a shortened string with ellipsis when needed."""
    s = str(v)
    return s if len(s) <= maxlen else s[: maxlen - 1] + "…"


def as_json(v: Any) -> str:
    """Render value as a compact JSON string."""
    try:
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(v)


def _to_local_tz(dt: datetime, tz: str = DEFAULT_TZ) -> datetime:
    """Normalize datetime to the desired timezone.

    - If dt is naive => treat as UTC (standard for backend apps)
    - If dt already has tzinfo => keep it and convert to the target tz
    """
    try:
        target = ZoneInfo(tz)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(target)
    except Exception as ex:
        _logger.error("err_to_local_tz", message=str(ex))
        return dt


def format_tz(
    dt: datetime | None,
    tz: str = DEFAULT_TZ,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format datetime to string according to the specified timezone + format."""
    if dt is None:
        return "-"
    try:
        local_dt = _to_local_tz(dt, tz)
        return local_dt.strftime(fmt)
    except Exception as ex:
        _logger.error("err_format_tz", message=str(ex))
        return str(dt)


def nested_number_lines(value: Any, prefix: str = "") -> list[str]:
    """Render nested value as numbered lines for templates."""
    try:
        from .nested_numbering import render_numbered_lines

        return render_numbered_lines(value, prefix)
    except Exception as ex:
        _logger.error("err_nested_number_lines", message=str(ex))
        return [str(value)]
