# tests/unit/flows/test_flow_sauce_demo_hooks.py
"""Unit tests for FLOW_SAUCE_DEMO hooks."""
# Why: keep input rules explicit for business reviewers.

from __future__ import annotations

import pytest

from engine.flows.flow_sauce_demo import hooks as sd_hooks


@pytest.mark.unit
def test_api_prevalidate_requires_products() -> None:
    """Missing product_names should be rejected."""
    errors = sd_hooks.api_prevalidate(
        [
            {
                "first_name": "A",
                "last_name": "B",
                "postal_code": "12345",
                "product_names": [],
            }
        ]
    )
    assert len(errors) == 1
    assert errors[0]["code"] == "NO_PRODUCTS"


@pytest.mark.unit
def test_validate_input_happy_path() -> None:
    """Valid payload should pass validate_input."""
    sd_hooks.validate_input(
        {
            "first_name": "John",
            "last_name": "Doe",
            "postal_code": "70000",
            "product_names": ["Sauce Labs Backpack"],
        }
    )


@pytest.mark.unit
def test_validate_input_rejects_invalid() -> None:
    """Invalid payload should raise to block bad jobs early."""
    with pytest.raises(ValueError, match="invalid_name"):
        sd_hooks.validate_input(
            {
                "first_name": "",
                "last_name": "Doe",
                "postal_code": "70000",
                "product_names": ["Sauce Labs Backpack"],
            }
        )
