# tests/unit/engine/orchestration/test_job_runner_hooks.py

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.orchestration import runner


class _InputModel(BaseModel):
    url: str | None = None


# WHY: Emulate hook lifecycle without executing real adapter side effects.
class _AdapterHooks:
    def __init__(self) -> None:
        self.before_job_payload: dict[str, Any] | None = None
        self.before_item_called = False
        self.after_job_summaries: list[dict[str, Any]] = []

    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.before_job_payload = payload
        return {"hook": "ctx"}

    def validate_input(self, raw: dict[str, Any]) -> None:
        raise AssertionError("validate_input should not be invoked")

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        self.before_item_called = True
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        raise AssertionError("on_retry should not be invoked")

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        raise AssertionError("on_error should not be invoked")

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        raise AssertionError("after_item should not be invoked")

    def after_job(self, ctx: dict[str, Any], summary: dict[str, Any]) -> None:
        self.after_job_summaries.append(summary)


class _Adapter:
    input_cls = _InputModel

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {}
        self.run_item_calls = 0

    def run_item(self, input_obj: _InputModel, page: object) -> None:
        self.run_item_calls += 1
        return None


pytestmark = pytest.mark.unit


def test_run_job_handles_empty_payloads(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(0)

    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    results = runner.run_job(flow=FlowType.CRAWL_SIMPLE, items=[], options={"job_id": "empty"})

    assert results == []
    assert adapter.hooks.before_job_payload is not None
    assert adapter.hooks.after_job_summaries == [{"done": 0, "failed": 0, "cancelled": 0}]
    assert adapter.hooks.before_item_called is False
    assert adapter.run_item_calls == 0
