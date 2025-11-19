# tests/integration/flows/test_flow_hooks_validation.py

"""Integration test verifying crawl_simple hook orchestration."""
# WHY: Hook ordering guards dedupe/validation consistency for JobRunner.

from __future__ import annotations

from collections import deque
from types import SimpleNamespace

import pytest

from engine.automation.playwright.session.context_factory import SessionBundle
from engine.core.constants.flows import FlowType
from engine.flows import registry

pytestmark = pytest.mark.integration


def test_validate_and_dedupe_across_items(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = registry.get_flow_adapter(FlowType.CRAWL_SIMPLE)
    bundle = SessionBundle(pw=None, browser=None, context=None)
    pages = deque(["page-1", "page-2"])
    closed: list[SessionBundle] = []

    monkeypatch.setattr(
        "engine.automation.playwright.session.build_session_bundle",
        lambda **kwargs: bundle,
    )
    monkeypatch.setattr(
        "engine.automation.playwright.session.ensure_page",
        lambda bundle, reuse: pages.popleft(),
    )
    monkeypatch.setattr(
        "engine.automation.playwright.session.close_bundle",
        lambda b: closed.append(b),
    )

    ctx = adapter.hooks.before_job({"spec": SimpleNamespace(context_per="JOB", page_reuse=False)})

    items = [
        {"url": "https://a.com", "meta": {"raw_text": "alpha"}},
        {"url": "https://b.com", "meta": {"raw_text": "beta"}},
    ]

    keys: list[str] = []
    for item in items:
        adapter.hooks.validate_input(item)
        page = adapter.hooks.before_item(ctx, item)
        assert page.startswith("page-")
        adapter.hooks.after_item(ctx, {"status": "DONE", "extras": {}})
        keys.append(adapter.hooks.dedupe_key(item))

    assert len(set(keys)) == 2

    with pytest.raises(ValueError, match="invalid_url"):
        adapter.hooks.validate_input({"url": "ftp://bad"})

    adapter.hooks.after_job(ctx, {"status": "DONE"})

    assert closed == [bundle]
    assert ctx["bundle"] is None
