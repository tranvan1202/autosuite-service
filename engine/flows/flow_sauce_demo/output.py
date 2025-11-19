# root/engine/flows/flow_sauce_demo/output.py
"""Output model for FLOW_SAUCE_DEMO."""
# Why: return exactly what a manual tester expects to read.

from __future__ import annotations

from pydantic import BaseModel, Field


class SauceDemoOutput(BaseModel):
    totals: dict[str, str] = Field(
        ..., description="Labels as displayed on UI"
    )  # {"item_total": "...", "tax": "...", "grand_total": "..."}
    selected_products: list[str] = Field(default_factory=list)
    customer: dict[str, str] = Field(
        default_factory=dict
    )  # {"first_name": ..., "last_name": ..., "postal_code": ...}
