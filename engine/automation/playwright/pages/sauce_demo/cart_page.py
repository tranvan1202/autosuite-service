# root/engine/automation/playwright/pages/sauce_demo/cart_page.py
"""Cart page: assertions and go to checkout."""
# Why: verify cart items match selection.

from __future__ import annotations

from typing import Any

from ...locators import sauce_demo as L
from .step_one_page import CheckoutStepOnePage


class CartPage:
    """Assert cart contents and proceed."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def assert_contains(self, expected_names: list[str]) -> CartPage:
        items = self.page.locator(L.L_CART_ITEM)
        found = [
            items.nth(i).locator(L.L_CART_NAME).inner_text().strip() for i in range(items.count())
        ]
        missing = set(expected_names) - set(found)
        if missing:
            raise RuntimeError(f"Cart missing: {sorted(missing)}")
        return self

    def checkout(self) -> CheckoutStepOnePage:
        self.page.click(L.L_BTN_CHECKOUT)
        self.page.wait_for_url(L.URL_STEP1)
        title = self.page.locator(L.L_TITLE).first.inner_text().strip()
        if title != "Checkout: Your Information":
            raise AssertionError("not_on_step_one")
        return CheckoutStepOnePage(self.page)
