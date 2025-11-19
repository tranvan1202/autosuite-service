# tests/integration/context/test_session_lifecycle.py

"""Integration test covering session lifecycle with flow hooks."""
# WHY: Ensuring bundle creation/teardown prevents Playwright leaks in CI.

from __future__ import annotations

import pytest

from engine.automation.playwright.session import context_factory
from engine.automation.playwright.session.context_factory import FlowSessionSpec
from engine.core.constants.flows import FlowType
from engine.flows import registry

pytestmark = pytest.mark.integration


def test_session_lifecycle_closes_resources(
    monkeypatch: pytest.MonkeyPatch, fake_playwright
) -> None:
    adapter = registry.get_flow_adapter(FlowType.CRAWL_SIMPLE)
    bundle = context_factory.build_session_bundle(
        headless=True,
        spec=FlowSessionSpec(
            mode=adapter.spec.mode,
            secret_names=list(adapter.spec.secret_names),
            page_reuse=adapter.spec.page_reuse,
        ),
    )

    monkeypatch.setattr(
        "engine.automation.playwright.session.build_session_bundle",
        lambda **kwargs: bundle,
    )
    monkeypatch.setattr(
        "engine.automation.playwright.session.ensure_page",
        context_factory.ensure_page,
    )
    monkeypatch.setattr(
        "engine.automation.playwright.session.close_bundle",
        context_factory.close_bundle,
    )

    ctx = adapter.hooks.before_job({"spec": adapter.spec})
    item = {"url": "https://example.com", "meta": {"raw_text": "alpha"}}

    adapter.hooks.validate_input(item)
    page = adapter.hooks.before_item(ctx, item)
    assert page.startswith("page-")
    adapter.hooks.after_item(ctx, {"status": "DONE", "extras": {}})
    adapter.hooks.after_job(ctx, {"status": "DONE"})

    assert fake_playwright.contexts[0].closed is True
    assert fake_playwright.closed is True
    assert ctx["bundle"] is None
