# root/engine/flows/flow_sauce_demo/run.py
from __future__ import annotations

from time import perf_counter
from typing import Any

import structlog

from ...automation.playwright.pages.sauce_demo.cart_page import CartPage
from ...automation.playwright.pages.sauce_demo.complete_page import CheckoutCompletePage
from ...automation.playwright.pages.sauce_demo.inventory_page import InventoryPage
from ...automation.playwright.pages.sauce_demo.login_page import LoginPage
from ...automation.playwright.pages.sauce_demo.step_one_page import CheckoutStepOnePage
from ...automation.playwright.pages.sauce_demo.step_two_page import CheckoutStepTwoPage
from ...core.config.loader import get_settings
from ...core.errors import ErrorCode
from ...core.models.action_result import ActionResult
from .input import SauceDemoInput
from .output import SauceDemoOutput

_logger = structlog.get_logger(__name__)


def run_item(input_: SauceDemoInput, page: Any) -> ActionResult[dict]:
    """Login → select products → cart → step1/2 → totals → complete."""

    t0 = perf_counter()
    timings: dict[str, float]
    try:
        # creds: dict[str, Any] = get_form_auth("sauce_demo")
        # username: str = (creds.get("username") or "") if creds else ""
        # password: str = (creds.get("password") or "") if creds else ""

        env_settings = get_settings()
        username: str = env_settings.saucedemo_username
        password: str = env_settings.saucedemo_pw

        # observability only (not domain data)
        asserted: dict[str, bool] = {}

        inv: InventoryPage = LoginPage(page).open().login(username, password)
        asserted["inventory"] = True

        cart: CartPage = inv.wait_loaded().add_products_by_name(input_.product_names).go_to_cart()
        cart.assert_contains(input_.product_names)
        asserted["cart"] = True

        step1: CheckoutStepOnePage = cart.checkout()
        asserted["step_one"] = True

        step2: CheckoutStepTwoPage = step1.fill_and_continue(
            input_.first_name, input_.last_name, input_.postal_code
        )
        step2.assert_contains(input_.product_names)
        totals = step2.read_totals()
        asserted["step_two"] = True

        complete: CheckoutCompletePage = step2.finish()
        complete.assert_success()
        asserted["complete"] = True
        value = SauceDemoOutput(
            totals=totals,
            selected_products=list(input_.product_names),
            customer={
                "first_name": input_.first_name,
                "last_name": input_.last_name,
                "postal_code": input_.postal_code,
            },
        ).model_dump()

        elapsed = perf_counter() - t0
        timings = {"total": elapsed}

        return ActionResult(ok=True, value=value, extras={"asserted": asserted}, timings=timings)

    except Exception as exc:
        _logger.warning("sauce_demo_failed", err=str(exc))
        elapsed = perf_counter() - t0
        timings = {"total": elapsed}
        return ActionResult(
            ok=False, error_code=ErrorCode.UNKNOWN, error_message=str(exc), timings=timings
        )
