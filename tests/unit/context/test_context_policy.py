# tests/unit/context/test_context_policy.py

"""Unit tests for Playwright session policy helpers."""
# WHY: Policy helpers guard lifecycle; stubbing them keeps behaviour observable.

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.automation.playwright.session import policy

pytestmark = pytest.mark.unit


def test_create_context_uses_profile_settings() -> None:
    captured: dict[str, object] = {}

    class FakeContext:
        def __init__(self) -> None:
            self.init_scripts: list[str] = []

        def add_init_script(self, script: str) -> None:
            self.init_scripts.append(script)

    class FakeBrowser:
        def new_context(self, **kwargs) -> FakeContext:  # type: ignore[override]
            captured.update(kwargs)
            return FakeContext()

    profile = {
        "user_agent": "ua",
        "locale": "en-US",
        "timezone_id": "Asia/Ho_Chi_Minh",
        "viewport": {"width": 1280, "height": 720},
        "device_scale_factor": 1.25,
        "is_mobile": False,
        "init_script": "console.log('pw')",
    }

    ctx = policy.create_context(FakeBrowser(), profile)

    assert captured["user_agent"] == "ua"
    assert captured["timezone_id"] == "Asia/Ho_Chi_Minh"
    assert ctx.init_scripts == ["console.log('pw')"]


def test_close_context_swallows_errors() -> None:
    class FakeContext:
        def close(self) -> None:
            raise RuntimeError("boom")

    policy.close_context(FakeContext())


def test_new_page_proxy() -> None:
    class FakeContext:
        def new_page(self) -> str:
            return "page"

    ctx = FakeContext()

    page = policy.new_page(ctx)

    assert page == "page"


def test_start_and_stop_tracing(tmp_path: Path) -> None:
    class FakeTracing:
        def __init__(self) -> None:
            self.started: list[dict[str, object]] = []
            self.stopped: list[str] = []

        def start(self, **kwargs) -> None:
            self.started.append(kwargs)

        def stop(self, *, path: str) -> None:
            self.stopped.append(path)

    tracing = FakeTracing()
    context = SimpleNamespace(tracing=tracing)
    out_path = tmp_path / "trace" / "flow" / "job" / "item-1.zip"

    policy.start_tracing(context)
    policy.stop_tracing(context, str(out_path))

    assert tracing.started == [{"screenshots": True, "snapshots": True, "sources": False}]
    assert tracing.stopped == [str(out_path)]
    assert out_path.parent.exists()
