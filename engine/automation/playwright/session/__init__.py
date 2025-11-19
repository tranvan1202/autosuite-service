# root/engine/automation/playwright/session/__init__.py
"""Public session helpers for Playwright engine."""
# Why: keep one stable import path for flows/hooks.

from __future__ import annotations

from .context_factory import (
    FlowSessionSpec,
    SessionBundle,
    build_session_bundle,
    close_bundle,
    ensure_page,
)

__all__ = [
    "FlowSessionSpec",
    "SessionBundle",
    "build_session_bundle",
    "close_bundle",
    "ensure_page",
]
