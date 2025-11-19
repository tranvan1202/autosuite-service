# root/engine/core/constants/flows.py
"""Declared flows to keep dispatch and docs in sync."""
# Why: adding a flow is a single-line change here then ripple safely.

from __future__ import annotations

from enum import StrEnum, unique


@unique
class FlowType(StrEnum):
    """visible flows;"""

    CRAWL_SIMPLE = "CRAWL_SIMPLE"
    FLOW_SAUCE_DEMO = "FLOW_SAUCE_DEMO"
