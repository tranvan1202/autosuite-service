# root/engine/automation/playwright/pages/sauce_demo/step_one_page.py
"""Checkout step one: fill form."""
# Why: separate data entry from navigation.

from __future__ import annotations

from typing import Any

from ...locators import sauce_demo as L
from .step_two_page import CheckoutStepTwoPage


class CheckoutStepOnePage:
    """Fill form and continue."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def fill_and_continue(self, first: str, last: str, zip_code: str) -> CheckoutStepTwoPage:
        self.page.fill(L.L_FIRST, first)
        self.page.fill(L.L_LAST, last)
        self.page.fill(L.L_ZIP, zip_code)
        self.page.click(L.L_BTN_CONTINUE)
        self.page.wait_for_url(L.URL_STEP2)
        return CheckoutStepTwoPage(self.page)
