# root/engine/automation/playwright/session/policy.py
"""Context/page lifecycle helpers."""
# Why: flows decide policy; this module enforces it predictably.

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

_logger = structlog.get_logger(__name__)


def create_context(browser: Any, profile: dict) -> Any:
    """Create a BrowserContext with a realistic profile."""
    context = browser.new_context(
        user_agent=profile.get("user_agent"),
        locale=profile.get("locale"),
        timezone_id=profile.get("timezone_id"),
        viewport=profile.get("viewport"),
        device_scale_factor=profile.get("device_scale_factor"),
        is_mobile=profile.get("is_mobile", False),
    )
    init_script = profile.get("init_script")
    if init_script:
        context.add_init_script(init_script)
    return context


def new_page(context: Any) -> Any:
    """Return a blank page ready for navigation."""
    return context.new_page()


def close_context(context: Any) -> None:
    """Close context safely."""
    try:
        context.close()
    except Exception as e:
        _logger.error("close_context_failed", err=str(e))


def close_page(page: Any) -> None:
    """Close page safely."""
    try:
        page.close()
    except Exception as e:
        _logger.error("close_page_failed", err=str(e))


# --- tracing helpers  ---


def start_tracing(context: Any) -> None:
    """Begin Playwright tracing for current item."""
    try:
        context.tracing.start(screenshots=True, snapshots=True, sources=False)
    except Exception as e:
        _logger.error("start_tracing_failed", err=str(e))


def stop_tracing(context: Any, out_path: str) -> None:
    """Stop tracing and persist trace.zip."""
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        context.tracing.stop(path=out_path)
    except Exception as e:
        _logger.error("stop_tracing_failed", err=str(e))
