# root/service/db/types.py
"""Cross-DB JSON type that maps to JSONB in PG and TEXT in SQLite."""
# Why: keep column names generic (input/output/timings/options) yet flexible.

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.engine import Dialect
from sqlalchemy.types import TEXT, TypeDecorator


class JSONFlex(TypeDecorator):
    """Serialize dict/list to TEXT; PG can swap to JSONB later."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value: str | None, dialect: Dialect) -> Any | None:
        if value is None:
            return None
        return json.loads(value)
