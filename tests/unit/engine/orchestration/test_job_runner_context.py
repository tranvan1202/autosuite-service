# tests/unit/engine/orchestration/test_job_runner_context.py

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.orchestration import runner


class _InputModel(BaseModel):
    url: str


# WHY: Track hook payload propagation to assert context reuse behaviour.
class _AdapterHooks:
    def __init__(self) -> None:
        self.before_item_contexts: list[dict[str, Any]] = []
        self.after_item_payloads: list[dict[str, Any]] = []

    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"from_hook": True}

    def validate_input(self, raw: dict[str, Any]) -> None:
        return None

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        self.before_item_contexts.append(dict(ctx))
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        return None

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        return None

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        self.after_item_payloads.append(dict(payload))

    def after_job(self, ctx: dict[str, Any], summary: dict[str, Any]) -> None:
        return None


class _Adapter:
    input_cls = _InputModel
    page_reuse = True

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {}
        self.run_item_calls = 0

    def run_item(self, input_obj: _InputModel, page: object) -> Any:
        self.run_item_calls += 1
        return _Result(value={"url": input_obj.url})


class _Result:
    def __init__(self, value: dict[str, Any]) -> None:
        self.ok = True
        self.value = value
        self.error_code = None
        self.error_message = None
        self.timings = {"duration": 1.0}
        self.extras: dict[str, Any] = {}


pytestmark = pytest.mark.unit


def test_run_job_adds_page_reuse_flag(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(0)

    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    results = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"url": "https://example.com"}],
        options={"job_id": "ctx"},
    )

    assert len(results) == 1
    assert results[0].status == ItemStatus.DONE
    assert adapter.hooks.before_item_contexts[0]["page_reuse"] is True
    assert adapter.hooks.before_item_contexts[0]["from_hook"] is True
    assert adapter.hooks.after_item_payloads[-1]["status"] == ItemStatus.DONE
