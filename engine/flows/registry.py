# root/engine/flows/registry.py
"""Flow registry to keep runner tiny and open for extension."""
# Why: adding a flow shouldn't touch orchestration; update one map and done.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..automation.playwright.session.context_factory import FlowSessionSpec
from ..core.constants.flows import FlowType
from ..core.constants.session import ContextPer, SessionMode


@dataclass(frozen=True, slots=True)
class FlowAdapter:
    """Entrypoints for a flow."""

    input_cls: type
    run_item: Callable[[Any, Any], Any]  # (input_obj, page) -> ActionResult[dict]
    hooks: Any  # module with required hook functions
    spec: FlowSessionSpec
    context_per: ContextPer
    page_reuse: bool


def get_flow_adapter(flow: FlowType) -> FlowAdapter:
    """Return the adapter + session spec for a flow."""
    if flow in {FlowType.CRAWL_SIMPLE}:
        from .crawl_simple import hooks as hooks_mod_cs, run as run_mod_cs
        from .crawl_simple.input import CrawlSimpleInput

        spec = FlowSessionSpec(
            mode=SessionMode.NON_AUTH,  # switch to COOKIES_AUTH for cookie flows
            secret_names=[],  # e.g., ["aem","jira"] when needed
            page_reuse=False,
        )

        return FlowAdapter(
            input_cls=CrawlSimpleInput,
            run_item=run_mod_cs.run_item,
            hooks=hooks_mod_cs,
            spec=spec,
            context_per=ContextPer.JOB,
            page_reuse=spec.page_reuse,
        )

    if flow in {FlowType.FLOW_SAUCE_DEMO}:
        from .flow_sauce_demo import hooks as hooks_mod_sm, run as run_mod_sm
        from .flow_sauce_demo.input import SauceDemoInput

        spec = FlowSessionSpec(
            mode=SessionMode.FORM_AUTH,  # login form with secrets fallback
            secret_names=["sauce_demo"],  # secrets/form_auth/sauce_demo.json (optional)
            page_reuse=False,  # new blank page per attempt
        )

        return FlowAdapter(
            input_cls=SauceDemoInput,
            run_item=run_mod_sm.run_item,
            hooks=hooks_mod_sm,
            spec=spec,
            context_per=ContextPer.JOB,
            page_reuse=spec.page_reuse,
        )

    raise ValueError(f"Unsupported flow: {flow}")
