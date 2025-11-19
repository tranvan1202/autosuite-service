# tests/integration/context/test_context_profile_integration.py

"""Integration tests for profile seeding and context creation."""
# WHY: Profile seed + factory output must align to keep browser fingerprint stable.

from __future__ import annotations

import pytest

from engine.automation.playwright.session import context_factory
from engine.automation.playwright.session.context_factory import FlowSessionSpec
from engine.core.constants.session import SessionMode

pytestmark = pytest.mark.integration


def test_build_session_bundle_applies_seed(fake_playwright) -> None:
    bundle = context_factory.build_session_bundle(
        headless=False,
        spec=FlowSessionSpec(mode=SessionMode.NON_AUTH, secret_names=[], page_reuse=False),
    )

    ctx = fake_playwright.contexts[0]
    assert bundle.browser is fake_playwright
    assert ctx.options["user_agent"] == "ua"
    assert ctx.options["timezone_id"] == "Asia/Ho_Chi_Minh"
    assert ctx.init_scripts == ["console.log('seed')"]
    assert fake_playwright.launch_args["headless"] is False
