# tests/unit/flows/test_flow_hooks.py
"""Unit tests for shared flow hook behaviours."""
# WHY: Hooks orchestrate expensive resources; mocking them prevents regressions.

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.automation.playwright.session.context_factory import SessionBundle
from engine.flows.crawl_simple import hooks as crawl_hooks

pytestmark = pytest.mark.unit


def _settings(headless: bool = True, tracing: str = "off") -> SimpleNamespace:
    return SimpleNamespace(pw_headless=headless, pw_tracing=tracing)


@pytest.fixture
def crawl_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(crawl_hooks, "get_settings", lambda: _settings())


def test_before_job_creates_bundle_when_context_per_job(monkeypatch, crawl_settings) -> None:
    fake_bundle = SessionBundle(pw=None, browser=None, context=None)

    def fake_builder(**kwargs):  # type: ignore[no-untyped-def]
        # WHY: Stub builder to avoid starting real Playwright.
        return fake_bundle

    monkeypatch.setattr(
        "engine.automation.playwright.session.build_session_bundle",
        fake_builder,
    )
    ctx = crawl_hooks.before_job({"spec": SimpleNamespace(context_per="JOB", page_reuse=False)})

    assert ctx["bundle"] is fake_bundle
    assert ctx["page_reuse"] is False


def test_after_job_closes_bundle(monkeypatch, crawl_settings) -> None:
    closed: list[SessionBundle] = []

    def fake_close(bundle: SessionBundle) -> None:
        closed.append(bundle)

    monkeypatch.setattr(
        "engine.automation.playwright.session.close_bundle",
        fake_close,
    )
    bundle = SessionBundle(pw=None, browser=None, context=None)
    ctx = {"bundle": bundle}

    crawl_hooks.after_job(ctx, {"status": "done"})

    assert closed == [bundle]
    assert ctx["bundle"] is None


def test_before_item_ensures_page(monkeypatch, crawl_settings) -> None:
    bundle = SessionBundle(pw=None, browser=None, context=None)

    def fake_ensure_page(bundle: SessionBundle, reuse: bool) -> str:  # type: ignore[override]
        # WHY: Return deterministic token to mimic Playwright page.
        return "fake-page"

    monkeypatch.setattr(
        "engine.automation.playwright.session.ensure_page",
        fake_ensure_page,
    )
    ctx = {"bundle": bundle, "page_reuse": True}

    page = crawl_hooks.before_item(ctx, {"url": "https://example.com"})

    assert page == "fake-page"
    assert ctx["page"] == "fake-page"


def test_dedupe_key_is_deterministic() -> None:
    item = {"url": "https://example.com", "meta": {"raw_text": "Hello"}}

    k1 = crawl_hooks.dedupe_key(item)
    k2 = crawl_hooks.dedupe_key(item)

    assert k1 == k2
