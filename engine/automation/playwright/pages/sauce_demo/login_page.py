# root/engine/automation/playwright/pages/sauce_demo/login_page.py
"""Login page object for Sauce Demo."""
# Why: isolate login so flows only choreograph steps.

from __future__ import annotations

from typing import Any

from ...locators import sauce_demo as L
from .inventory_page import InventoryPage


class LoginPage:
    """Open login and submit credentials."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def open(self) -> LoginPage:
        """Navigate to login URL and return self."""
        self.page.goto(L.URL_LOGIN, wait_until="domcontentloaded")
        return self

    def login(self, username: str, password: str) -> InventoryPage:
        """Submit credentials and assert we land on Inventory."""
        self.page.fill(L.L_USERNAME_LOCATOR, username)
        self.page.fill(L.L_PASSWORD_LOCATOR, password)
        self.page.click(L.L_BTN_LOGIN)
        self.page.wait_for_selector(f"{L.L_INV_GUARD}, {L.L_LOGIN_ERR}", timeout=10_000)
        if self.page.locator(L.L_LOGIN_ERR).first.is_visible():
            raise RuntimeError(self.page.locator(L.L_LOGIN_ERR).inner_text().strip())
        self.page.wait_for_url("**/inventory.html")
        title = self.page.locator(L.L_TITLE).first.inner_text().strip()
        if title != "Products":
            raise AssertionError("not_on_inventory")
        return InventoryPage(self.page)
