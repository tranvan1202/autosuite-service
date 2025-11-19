# tests/integration/flows/test_flow_sauce_demo_retries.py

"""Integration test covering sauce demo retry behaviour."""
# WHY: Sauce Demo flow is business-critical; simulate failure without real browser.

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.automation.playwright.session import injectors
from engine.flows.flow_sauce_demo import hooks as sauce_hooks, run as sauce_run
from engine.flows.flow_sauce_demo.input import SauceDemoInput

pytestmark = pytest.mark.integration


class _FailingInventory:
    def wait_loaded(self) -> _FailingInventory:
        return self

    def add_products_by_name(self, names: list[str]) -> _FailingInventory:
        return self

    def go_to_cart(self) -> _FailingInventory:
        raise RuntimeError("inventory not ready")


class _FailingLogin:
    def __init__(self, page: object) -> None:
        self.page = page

    def open(self) -> _FailingLogin:
        return self

    def login(self, username: str, password: str) -> _FailingInventory:
        # WHY: Force failure after credential use to trigger ActionResult error path.
        return _FailingInventory()


def test_run_item_failure_and_retry_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sauce_run, "LoginPage", _FailingLogin)
    monkeypatch.setattr(
        injectors, "get_form_auth", lambda *names: {"username": "u", "password": "p"}
    )

    payload = SauceDemoInput(
        first_name="Ada",
        last_name="Lovelace",
        postal_code="700000",
        product_names=["Sauce Labs Backpack"],  # WHY: Use FE dropdown name for regression fidelity.
    )

    result = sauce_run.run_item(payload, SimpleNamespace())

    assert result.ok is False
    assert result.error_code.name == "UNKNOWN"

    sauce_hooks.on_retry(payload.model_dump(), attempt=1, error=RuntimeError("inventory not ready"))
