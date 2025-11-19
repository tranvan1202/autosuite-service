# root/engine/automation/playwright/pages/sauce_demo/step_two_page.py
"""Checkout step two: verify and finish."""
# Why: totals should be read as displayed to avoid float issues.

from __future__ import annotations

from typing import Any

from ...locators import sauce_demo as L
from .complete_page import CheckoutCompletePage


class CheckoutStepTwoPage:
    """Re-assert items, read totals, and finish."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def assert_contains(self, expected_names: list[str]) -> CheckoutStepTwoPage:
        items = self.page.locator(L.L_STEP2_ITEM)
        found = [
            items.nth(i).locator(L.L_STEP2_NAME).inner_text().strip() for i in range(items.count())
        ]
        missing = set(expected_names) - set(found)
        if missing:
            raise RuntimeError(f"Step Two missing: {sorted(missing)}")
        return self

    def read_totals(self) -> dict[str, str]:
        return {
            "item_total": self.page.locator(L.L_SUBTOTAL).inner_text().strip(),
            "tax": self.page.locator(L.L_TAX).inner_text().strip(),
            "grand_total": self.page.locator(L.L_TOTAL).inner_text().strip(),
        }

    def finish(self) -> CheckoutCompletePage:
        self.page.click(L.L_BTN_FINISH)
        self.page.wait_for_url("**/checkout-complete.html")
        return CheckoutCompletePage(self.page)
