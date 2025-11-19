# root/engine/flows/crawl_simple/output.py
"""Output contract for CRAWL_SIMPLE."""
# Why: a stable schema simplifies exporters and assertions.

from __future__ import annotations

from pydantic import BaseModel, Field


class CrawlSimpleOutput(BaseModel):
    """Minimal page facts for smoke-quality insights."""

    title: str | None
    final_url: str | None
    http_status: int | None
    meta_tags: dict[str, str] = Field(default_factory=dict)
    meta: dict[str, object] = Field(default_factory=dict)
