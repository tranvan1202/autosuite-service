# root/tests/unit/engine/flows/flow_sauce_demo/test_hooks_validation.py
from __future__ import annotations

import pytest

from engine.flows.flow_sauce_demo import hooks


@pytest.mark.unit
def test_field_options_has_product_names_list():
    opts = hooks.field_options()
    assert "product_names" in opts
    assert isinstance(opts["product_names"], list)
    assert "Sauce Labs Backpack" in opts["product_names"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "item, expected_codes",
    [
        (
            {},  # thiếu hết
            {"MISSING_REQUIRED", "NO_PRODUCTS"},
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "postal_code": "12345",
                "product_names": [],
            },
            {"NO_PRODUCTS"},
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "postal_code": "12345",
                "product_names": ["A"],
            },
            set(),
        ),
    ],
)
def test_api_prevalidate_collects_errors(item, expected_codes):
    errors = hooks.api_prevalidate([item])
    codes = {e["code"] for e in errors}
    assert codes == expected_codes


@pytest.mark.unit
def test_validate_input_ok():
    hooks.validate_input(
        {
            "first_name": "John",
            "last_name": "Doe",
            "postal_code": "94105",
            "product_names": ["Sauce Labs Backpack"],
        }
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload, expected_message",
    [
        (
            {
                "first_name": "",
                "last_name": "Doe",
                "postal_code": "94105",
                "product_names": ["X"],
            },
            "invalid_name",
        ),
        (
            {
                "first_name": "John",
                "last_name": "D@e!",
                "postal_code": "94105",
                "product_names": ["X"],
            },
            "invalid_name",
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "postal_code": "!!",
                "product_names": ["X"],
            },
            "invalid_postal_code",
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "postal_code": "94105",
                "product_names": [],
            },
            "invalid_product_names",
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "postal_code": "94105",
                "product_names": ["X"] * 11,
            },
            "too_many_products",
        ),
    ],
)
def test_validate_input_invalid_cases(payload, expected_message):
    with pytest.raises(ValueError, match=expected_message) as excinfo:
        hooks.validate_input(payload)
    assert str(excinfo.value) == expected_message
