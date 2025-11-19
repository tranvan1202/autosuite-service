"""Unit tests for Playwright session factory helpers."""

# WHY: Factory stubs must remain deterministic to keep CI fast without browsers.

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.automation.playwright.session import context_factory
from engine.automation.playwright.session.context_factory import FlowSessionSpec, SessionBundle
from engine.core.constants.session import SessionMode

pytestmark = pytest.mark.unit


def test_build_session_bundle_creates_browser_context(monkeypatch: pytest.MonkeyPatch) -> None:
    launched: dict[str, object] = {}
    fake_browser = SimpleNamespace()
    fake_context = object()

    def fake_start() -> SimpleNamespace:
        def launch(*, headless: bool) -> SimpleNamespace:  # type: ignore[override]
            launched["headless"] = headless
            return fake_browser

        return SimpleNamespace(chromium=SimpleNamespace(launch=launch))

    def fake_sync_playwright() -> SimpleNamespace:
        return SimpleNamespace(start=fake_start)

    def fake_create_context(browser: object, profile: dict) -> object:
        launched["browser"] = browser
        launched["profile"] = profile
        return fake_context

    monkeypatch.setattr(context_factory, "sync_playwright", fake_sync_playwright)
    monkeypatch.setattr(context_factory.policy, "create_context", fake_create_context)
    monkeypatch.setattr(context_factory, "make_seed", lambda seed=None: {"user_agent": "ua"})

    bundle = context_factory.build_session_bundle(
        headless=False,
        spec=FlowSessionSpec(mode=SessionMode.NON_AUTH, secret_names=[], page_reuse=False),
    )

    assert isinstance(bundle, SessionBundle)
    assert launched["headless"] is False
    assert launched["browser"] is fake_browser
    assert launched["profile"] == {"user_agent": "ua"}
    assert bundle.context is fake_context


def test_ensure_page_respects_reuse(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[str] = []

    def fake_new_page(context: object) -> str:
        created.append("new")
        return "page"

    monkeypatch.setattr(context_factory.policy, "new_page", fake_new_page)
    bundle = SessionBundle(pw=None, browser=None, context=object(), page=None)

    first = context_factory.ensure_page(bundle, reuse=True)
    second = context_factory.ensure_page(bundle, reuse=True)

    assert first == "page"
    assert second == "page"
    assert created == ["new"]


def test_close_bundle_closes_context_and_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeBrowser:
        def close(self) -> None:
            events.append("browser_close")

    class FakeContext:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            events.append("context_close")
            self.closed = True

    class FakePlaywright:
        def stop(self) -> None:
            events.append("pw_stop")

    bundle = SessionBundle(pw=FakePlaywright(), browser=FakeBrowser(), context=FakeContext())

    def fake_close_context(context: FakeContext) -> None:
        events.append("policy_close")
        context.close()

    monkeypatch.setattr(context_factory.policy, "close_context", fake_close_context)

    context_factory.close_bundle(bundle)

    assert events == ["policy_close", "context_close", "browser_close", "pw_stop"]
