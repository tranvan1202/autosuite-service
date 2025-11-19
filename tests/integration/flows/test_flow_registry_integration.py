# # tests/integration/flows/test_flow_registry_integration.py
#
# """Integration tests for flow registry and adapter wiring."""
# # WHY: Registry + adapter glue must deliver secrets and run chains correctly.
#
# from __future__ import annotations
#
# from types import SimpleNamespace
#
# import pytest
#
# from engine.automation.playwright.session import injectors
# from engine.core.constants.flows import FlowType
# from engine.flows import registry
# from engine.flows.flow_sauce_demo import run as sauce_run
# from engine.flows.flow_sauce_demo.input import SauceDemoInput
#
# pytestmark = pytest.mark.integration
#
#
# class _InventoryPage:
#     def __init__(self, page: object | None = None) -> None:
#         self.page = page
#         self.names: list[str] = []
#
#     def wait_loaded(self) -> _InventoryPage:
#         return self
#
#     def add_products_by_name(self, names: list[str]) -> _InventoryPage:
#         self.names = names
#         return self
#
#     def go_to_cart(self) -> _CartPage:
#         return _CartPage(self.names)
#
#
# class _CartPage:
#     def __init__(self, names: list[str]) -> None:
#         self.names = names
#
#     def assert_contains(self, names: list[str]) -> None:
#         assert names == self.names
#
#     def checkout(self) -> _CheckoutStepOnePage:
#         return _CheckoutStepOnePage(self.names)
#
#
# class _CheckoutStepOnePage:
#     def __init__(self, names: list[str]) -> None:
#         self.names = names
#
#     def fill_and_continue(self, first: str, last: str, postal: str) -> _CheckoutStepTwoPage:
#         return _CheckoutStepTwoPage(self.names)
#
#
# class _CheckoutStepTwoPage:
#     def __init__(self, names: list[str]) -> None:
#         self.names = names
#
#     def assert_contains(self, names: list[str]) -> None:
#         assert names == self.names
#
#     def read_totals(self) -> dict[str, str]:
#         return {"subtotal": "42.00"}
#
#     def finish(self) -> _CheckoutCompletePage:
#         return _CheckoutCompletePage()
#
#
# class _CheckoutCompletePage:
#     def assert_success(self) -> None:
#         return None
#
#
# class _LoginPage:
#     def __init__(self, page: object) -> None:
#         self.page = page
#
#     def open(self) -> _LoginPage:
#         return self
#
#     def login(self, username: str, password: str) -> _InventoryPage:
#         _CAPTURE["creds"] = (username, password)
#         return _InventoryPage()
#
#
# _CAPTURE: dict[str, object] = {}
#
#
# def test_registry_adapter_runs_flow_with_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
#     _CAPTURE.clear()
#     monkeypatch.setattr(sauce_run, "LoginPage", _LoginPage)
#     monkeypatch.setattr(sauce_run, "InventoryPage", _InventoryPage)
#     monkeypatch.setattr(sauce_run, "CheckoutStepOnePage", _CheckoutStepOnePage)
#     monkeypatch.setattr(sauce_run, "CheckoutStepTwoPage", _CheckoutStepTwoPage)
#     monkeypatch.setattr(sauce_run, "CheckoutCompletePage", _CheckoutCompletePage)
#     monkeypatch.setattr(
#         injectors,
#         "get_form_auth",
#         lambda *names: {"username": "standard_user", "password": "secret_sauce"},
#     )
#
#     adapter = registry.get_flow_adapter(FlowType.FLOW_SAUCE_DEMO)
#     payload = SauceDemoInput(
#         first_name="Ada",
#         last_name="Lovelace",
#         postal_code="700000",
#         product_names=["Sauce Labs Backpack"],
#     )
#
#     result = adapter.run_item(payload, SimpleNamespace())
#
#     assert result.ok is True
#     assert _CAPTURE["creds"] == ("standard_user", "secret_sauce")
#     assert result.value["selected_products"] == ["Sauce Labs Backpack"]
#     assert result.value["totals"] == {"subtotal": "42.00"}
