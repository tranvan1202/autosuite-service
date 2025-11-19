# root/engine/automation/playwright/pages/sauce_demo/complete_page.py
"""Completion page: final assertion."""
# Why: explicit end-state check aids debugging.

from __future__ import annotations

from typing import Any

from ...locators import sauce_demo as L


class CheckoutCompletePage:
    """Verify thank-you content is visible."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def assert_success(self) -> CheckoutCompletePage:
        assert self.page.locator(L.L_COMPLETE_HEADER).first.is_visible()
        assert self.page.locator(L.L_COMPLETE_TEXT).first.is_visible()
        return self
