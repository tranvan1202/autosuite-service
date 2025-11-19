# tests/integration/flows/test_crawl_simple_run_item.py

"""Integration tests for crawl_simple run_item."""
# WHY: Validating ActionResult keeps JobRunner outputs predictable.

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.flows.crawl_simple import run as crawl_run
from engine.flows.crawl_simple.input import CrawlSimpleInput

pytestmark = pytest.mark.integration


class _FakeCommonPage:
    def __init__(self, page: object) -> None:
        self.page = page

    def navigate_and_collect(self, url: str) -> dict[str, object]:
        return {
            "title": "Example",
            "final_url": url,
            "http_status": 200,
            "meta_tags": {"og:title": "Example"},
            "meta": {"raw": "data"},
        }


def test_run_item_returns_expected_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(crawl_run, "CommonPage", _FakeCommonPage)

    payload = CrawlSimpleInput(url="https://example.com", meta={"job_id": "job-1"})
    result = crawl_run.run_item(payload, SimpleNamespace())

    assert result.ok is True
    assert result.value["final_url"] == "https://example.com"
    assert result.value["meta_tags"]["og:title"] == "Example"
    assert result.timings["total"] >= 0
