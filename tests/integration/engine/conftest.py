# root/tests/integration/engine/conftest.py
"""Shared fakes for engine integration tests."""
# Why: keep tests focused on behavior, not plumbing.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from engine.core.constants.flows import FlowType
from engine.core.models.action_result import ActionResult


@dataclass
class FakeSpec:
    """Minimal spec for runner wiring."""

    context_per: str = "JOB"
    page_reuse: bool = False


class BaseFakeHooks:
    """No-op hooks so we only test runner orchestration."""

    def before_job(self, context: dict[str, Any]) -> dict[str, Any]:
        return {}

    def after_job(self, ctx: dict[str, Any], summary: dict[str, Any]) -> None:
        ctx["summary"] = summary

    def before_item(self, ctx: dict[str, Any], item_input: dict[str, Any]) -> Any:
        return None

    def after_item(self, ctx: dict[str, Any], item_result: dict[str, Any]) -> None:
        ctx["last_status"] = item_result.get("status")

    def api_prevalidate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return []

    def validate_input(self, item_input: dict[str, Any]) -> None:
        # Flows override where needed.
        return None

    def on_retry(self, item_input: dict[str, Any], attempt: int, error: Exception) -> None:
        item_input["__retry_calls__"] = item_input.get("__retry_calls__", []) + [attempt]

    def on_error(self, item_input: dict[str, Any], error: Exception) -> None:
        item_input["__errors__"] = item_input.get("__errors__", []) + [str(error)]

    def dedupe_key(self, item: dict[str, Any]) -> str:
        return item.get("url", "")


class FakeInput:
    """Very small input model used by fake adapters."""

    def __init__(self, url: str):
        self.url = url


class AllOkAdapter:
    """Fake adapter: every item succeeds."""

    input_cls = FakeInput
    hooks = BaseFakeHooks()
    spec = FakeSpec()

    def run_item(self, input_obj: FakeInput, page: Any) -> ActionResult[dict[str, Any]]:
        return ActionResult(ok=True, value={"url": input_obj.url, "ok": True})


class MixedAdapter:
    """Fake adapter: used to exercise dedupe + failures + validation."""

    input_cls = FakeInput
    hooks = BaseFakeHooks()
    spec = FakeSpec()

    def run_item(self, input_obj: FakeInput, page: Any) -> ActionResult[dict[str, Any]]:
        url = input_obj.url
        if "fail" in url:
            return ActionResult(ok=False, error_message="boom")
        return ActionResult(ok=True, value={"url": url})


@pytest.fixture
def patch_all_ok_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route CRAWL_SIMPLE to AllOkAdapter."""

    def _factory(flow: FlowType) -> Any:
        return AllOkAdapter()

    monkeypatch.setattr(
        "engine.flows.registry.get_flow_adapter",
        _factory,
    )


@pytest.fixture
def patch_mixed_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route CRAWL_SIMPLE to MixedAdapter."""

    def _factory(flow: FlowType) -> Any:
        return MixedAdapter()

    monkeypatch.setattr(
        "engine.flows.registry.get_flow_adapter",
        _factory,
    )
