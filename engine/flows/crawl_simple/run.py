# root/engine/flows/crawl_simple/run.py
"""Single-item runner for CRAWL_SIMPLE (Page-based)."""
# Why: flows should not spin browsers; they receive a blank page.

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter
from typing import Any, cast

import structlog

from ...automation.playwright.pages.common_page import CommonPage
from ...core.config.loader import get_settings
from ...core.errors import ErrorCode
from ...core.models.action_result import ActionResult
from .input import CrawlSimpleInput
from .output import CrawlSimpleOutput

_logger = structlog.get_logger(__name__)


def run_item(input_: CrawlSimpleInput, page: Any) -> ActionResult[dict]:
    """Navigate on provided page and return a minimal snapshot."""
    _logger.warning("start_flow_actions", url=input_.url)
    _ = get_settings()
    t0 = perf_counter()
    timings: dict[str, float]
    try:
        common = CommonPage(page)
        page_snapshot = common.navigate_and_collect(input_.url)
        _logger.warning("end_flow_actions", url=input_.url)

        title = cast(str | None, page_snapshot.get("title"))
        final_url = cast(str | None, page_snapshot.get("final_url"))
        http_status = cast(int | None, page_snapshot.get("http_status"))
        meta_tags = cast(Mapping[str, str] | dict[str, str] | None, page_snapshot.get("meta_tags"))

        page_snapshot["meta"] = input_.meta
        meta = cast(Mapping[str, Any] | dict[str, Any] | None, page_snapshot.get("meta"))

        elapsed = perf_counter() - t0
        timings = {"total": elapsed}
        page_snapshot["timings"] = timings

        value = CrawlSimpleOutput(
            title=title,
            final_url=final_url,
            http_status=http_status,
            meta_tags=dict(meta_tags or {}),
            meta=dict(meta or {}),
        ).model_dump()

        return ActionResult(ok=True, value=value, timings=timings)
    except Exception as exc:
        elapsed = perf_counter() - t0
        timings = {"total": elapsed}
        _logger.warning("crawl_simple_failed", url=input_.url, err=str(exc))
        return ActionResult(
            ok=False, error_code=ErrorCode.UNKNOWN, error_message=str(exc), timings=timings
        )
