# root/engine/automation/playwright/session/context_factory.py
"""Build/close a session bundle according to a FlowSessionSpec."""
# Why: runner gets one entry to create a ready-to-use blank page.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from playwright.sync_api import sync_playwright

from ....core.constants.session import SessionMode
from . import injectors, policy
from .seed import make_seed

_logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class FlowSessionSpec:
    """Flow intent for context construction."""

    mode: SessionMode  # NON_AUTH | COOKIES_AUTH | FORM_AUTH
    secret_names: list[str]  # e.g., ["aem","jira"] for cookies/auth
    page_reuse: bool


@dataclass(slots=True)
class SessionBundle:
    """Lifetime of Playwright objects for a job."""

    pw: Any
    browser: Any
    context: Any
    page: Any | None = None


def build_session_bundle(
    headless: bool,
    spec: FlowSessionSpec,
    seed_value: int | None = None,
) -> SessionBundle:
    """Create browser+context, inject profile/cookies, yield blank page."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    profile = make_seed(seed_value)
    context = policy.create_context(browser, profile)

    if spec.mode == SessionMode.COOKIES_AUTH and spec.secret_names:
        injectors.inject_cookies(context, *spec.secret_names)

    # For FORM_AUTH we only prepare context; flows decide when to call get_form_auth()
    bundle = SessionBundle(pw=pw, browser=browser, context=context)
    _logger.info("session_built", mode=spec.mode, secrets=len(spec.secret_names), headless=headless)
    return bundle


def ensure_page(bundle: SessionBundle, reuse: bool) -> Any:
    """Return an existing or a new blank page depending on reuse flag."""
    if reuse and bundle.page is not None:
        return bundle.page
    page = policy.new_page(bundle.context)
    if reuse:
        bundle.page = page
    return page


def close_bundle(bundle: SessionBundle) -> None:
    """Cleanup in reverse order; swallow close errors."""
    try:
        if bundle.context:
            policy.close_context(bundle.context)
        if bundle.browser:
            bundle.browser.close()
    except Exception as e:
        _logger.error("close_bundle_failed", err=str(e))
    finally:
        try:
            if bundle.pw:
                bundle.pw.stop()
        except Exception as e:
            _logger.error("close_bundle_pw_failed", err=str(e))
