# root/engine/automation/playwright/pages/sauce_demo/inventory_page.py
"""Inventory page: add products and go to cart."""
# Why: keep product-selection logic in one place.

from __future__ import annotations

from typing import Any

from ...locators import sauce_demo as L
from .cart_page import CartPage


class InventoryPage:
    """Select products by visible name."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def wait_loaded(self) -> InventoryPage:
        self.page.wait_for_selector(L.L_INV_LIST)
        return self

    def add_products_by_name(self, names: list[str]) -> InventoryPage:
        remaining = set(names)
        cards = self.page.locator(L.L_CARD)
        for i in range(cards.count()):
            title = cards.nth(i).locator(L.L_NAME).inner_text().strip()
            if title in remaining:
                cards.nth(i).locator(L.L_ADD_BTN).click()
                remaining.remove(title)
                if not remaining:
                    break
        if remaining:
            raise RuntimeError(f"Can't find the inputted products: {sorted(remaining)}")
        return self

    def go_to_cart(self) -> CartPage:
        self.page.click(L.L_CART_ICON)
        self.page.wait_for_url("**/cart.html")
        return CartPage(self.page)
