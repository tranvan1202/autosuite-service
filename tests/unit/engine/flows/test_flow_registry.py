# tests/unit/flows/test_flow_registry.py

"""Unit tests for flow registry mapping to adapters."""
# WHY: Registry dispatch errors can brick orchestration, so we lock expected metadata.

from __future__ import annotations

import pytest

from engine.core.constants.session import SessionMode
from engine.flows import registry
from engine.flows.crawl_simple import hooks as crawl_hooks, run as crawl_run
from engine.flows.crawl_simple.input import CrawlSimpleInput
from engine.flows.flow_sauce_demo import hooks as sauce_hooks, run as sauce_run
from engine.flows.flow_sauce_demo.input import SauceDemoInput

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "identifier, expected_cls, expected_run, expected_hooks",
    [
        (registry.FlowType.CRAWL_SIMPLE, CrawlSimpleInput, crawl_run.run_item, crawl_hooks),
        ("CRAWL_SIMPLE", CrawlSimpleInput, crawl_run.run_item, crawl_hooks),
        (
            registry.FlowType.FLOW_SAUCE_DEMO,
            SauceDemoInput,
            sauce_run.run_item,
            sauce_hooks,
        ),
        ("FLOW_SAUCE_DEMO", SauceDemoInput, sauce_run.run_item, sauce_hooks),
    ],
)
def test_get_flow_adapter_returns_expected_adapter(
    identifier, expected_cls, expected_run, expected_hooks
) -> None:
    adapter = registry.get_flow_adapter(identifier)

    assert adapter.input_cls is expected_cls
    assert adapter.run_item is expected_run
    assert adapter.hooks is expected_hooks
    assert adapter.page_reuse is adapter.spec.page_reuse


@pytest.mark.parametrize(
    "identifier, secret_names, expected_mode",
    [
        (registry.FlowType.CRAWL_SIMPLE, [], SessionMode.NON_AUTH),
        (registry.FlowType.FLOW_SAUCE_DEMO, ["sauce_demo"], SessionMode.FORM_AUTH),
    ],
)
def test_flow_adapter_spec_contains_expected_metadata(
    identifier, secret_names, expected_mode
) -> None:
    adapter = registry.get_flow_adapter(identifier)

    assert adapter.spec.secret_names == secret_names
    assert adapter.context_per.value == "JOB"
    assert adapter.spec.mode is expected_mode


def test_get_flow_adapter_unknown_flow_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported flow: UNKNOWN_FLOW"):
        registry.get_flow_adapter("UNKNOWN_FLOW")
