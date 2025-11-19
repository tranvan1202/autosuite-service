# tests/integration/context/conftest.py

"""Fixtures for context orchestration integration tests."""
# WHY: Session orchestration touches Playwright; shared stubs keep flows hermetic.

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.automation.playwright.session import context_factory


class _FakeContext:
    def __init__(self) -> None:
        self.closed = False
        self.new_page_calls: int = 0
        self.init_scripts: list[str] = []
        self.tracing = SimpleNamespace(start=lambda **_: None, stop=lambda **_: None)

    def add_init_script(self, script: str) -> None:
        self.init_scripts.append(script)

    def new_page(self) -> str:
        self.new_page_calls += 1
        return f"page-{self.new_page_calls}"

    def close(self) -> None:
        self.closed = True


class _FakeBrowser:
    def __init__(self) -> None:
        self.launch_args: dict[str, object] = {}
        self.closed = False
        self.contexts: list[_FakeContext] = []

    def new_context(self, **kwargs) -> _FakeContext:  # type: ignore[override]
        ctx = _FakeContext()
        ctx.options = kwargs  # type: ignore[attr-defined]
        self.contexts.append(ctx)
        return ctx

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_playwright(monkeypatch: pytest.MonkeyPatch) -> _FakeBrowser:
    browser = _FakeBrowser()

    def fake_start() -> SimpleNamespace:
        def launch(*, headless: bool) -> _FakeBrowser:  # type: ignore[override]
            browser.launch_args["headless"] = headless
            return browser

        return SimpleNamespace(chromium=SimpleNamespace(launch=launch), stop=lambda: None)

    monkeypatch.setattr(
        context_factory, "sync_playwright", lambda: SimpleNamespace(start=fake_start)
    )
    monkeypatch.setattr(
        context_factory,
        "make_seed",
        lambda seed=None: {
            "user_agent": "ua",
            "locale": "en-US",
            "timezone_id": "Asia/Ho_Chi_Minh",
            "viewport": {"width": 1280, "height": 720},
            "device_scale_factor": 1.25,
            "is_mobile": False,
            "init_script": "console.log('seed')",
        },
    )
    return browser
