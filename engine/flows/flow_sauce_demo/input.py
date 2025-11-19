# root/engine/flows/flow_sauce_demo/input.py
"""Input model for FLOW_SAUCE_DEMO."""
# Why: explicit schema makes validation and dedupe trivial.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

_NAME_RE = r"^[\w\s\-\.\']{1,50}$"
_POSTAL_RE = r"^[A-Za-z0-9\-\s]{3,12}$"


class SauceDemoInput(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, pattern=_NAME_RE)
    last_name: str = Field(..., min_length=1, max_length=50, pattern=_NAME_RE)
    postal_code: str = Field(..., min_length=3, max_length=12, pattern=_POSTAL_RE)
    product_names: list[str] = Field(
        default_factory=list, description="Visible product names to add"
    )
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("product_names")
    @classmethod
    def _validate_products(cls, v: list[str]) -> list[str]:
        # Keep it simple here: non-empty list, trim items, no empties, cap length.
        items = [s.strip() for s in v if str(s).strip()]
        if not items:
            raise ValueError("product_names must contain at least 1 item")
        if len(items) > 10:
            raise ValueError("too many product names (max 10)")
        return items
