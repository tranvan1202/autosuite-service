# tests/unit/flows/test_flow_inputs.py

"""Unit tests for flow input models."""
# WHY: Input schemas guard API contracts; regression keeps flows stable.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from engine.flows.crawl_simple.input import CrawlSimpleInput
from engine.flows.flow_sauce_demo.input import SauceDemoInput

pytestmark = pytest.mark.unit


def test_crawl_simple_input_accepts_url_and_defaults_meta() -> None:
    payload = {"url": "https://example.com"}

    model = CrawlSimpleInput.model_validate(payload)

    assert model.url == "https://example.com"
    assert model.meta == {}


def test_crawl_simple_input_empty_url_raises_validation_error() -> None:
    payload = {"url": ""}

    with pytest.raises(ValidationError, match="String should have at least"):
        CrawlSimpleInput.model_validate(payload)


def test_sauce_demo_input_trims_products_and_returns_clean_model() -> None:
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "postal_code": "700000",
        "product_names": [
            "  Sauce Labs Backpack  ",
            "Sauce Labs Bike Light",
        ],  # WHY: Use real catalog names to mirror FE dropdown.
    }

    model = SauceDemoInput.model_validate(payload)

    assert model.product_names == ["Sauce Labs Backpack", "Sauce Labs Bike Light"]


@pytest.mark.parametrize(
    "field, value, match",
    [
        ("first_name", "", "String should have at least"),
        ("last_name", "", "String should have at least"),
        ("postal_code", "??#", "String should match pattern"),
        ("product_names", [], "must contain at least 1"),
    ],
)
def test_sauce_demo_input_invalid_fields_raise_validation_error(field, value, match) -> None:
    base = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "postal_code": "700000",
        "product_names": ["Sauce Labs Backpack"],
    }
    base[field] = value

    with pytest.raises(ValidationError, match=match):
        SauceDemoInput.model_validate(base)
