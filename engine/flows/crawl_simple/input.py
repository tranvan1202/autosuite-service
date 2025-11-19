# root/engine/flows/crawl_simple/input.py
"""Input model for CRAWL_SIMPLE (Pydantic v2)."""
# Why: flows must expose Pydantic schemas for /flows/{slug}/input-spec.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CrawlSimpleInput(BaseModel):
    url: str = Field(..., min_length=4, description="Target URL")
    meta: dict[str, Any] = Field(default_factory=dict, description="Raw input")
