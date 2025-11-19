# tests/integration/engine/orchestration/test_job_runner_hooks_mutation.py

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.core.errors import ErrorCode
from engine.orchestration import runner

pytestmark = pytest.mark.integration


class _InputModel(BaseModel):
    url: str


class _Result:
    def __init__(self) -> None:
        self.ok = True
        self.value = {"url": "https://mutate.test"}
        self.error_code = ErrorCode.NONE
        self.error_message = None
        self.timings = {"duration": 0.1}
        self.extras: dict[str, Any] = {}


class _AdapterHooks:
    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate_input(self, raw: dict[str, Any]) -> None:
        return None

    def dedupe_key(self, raw: dict[str, Any]) -> str:
        return raw["url"]

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        return None

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        return None

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        payload.setdefault("extras", {})["source"] = "hook"
        payload.setdefault("timings", {})["duration"] = 1.23

    def after_job(self, ctx: dict[str, Any], summary: dict[str, int]) -> None:
        return None


class _Adapter:
    input_cls = _InputModel

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {"id": "mutate"}

    def run_item(self, input_obj: _InputModel, page: object) -> _Result:
        return _Result()


def test_hooks_mutation_persisted_in_results(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(0)
    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    # WHY: Deterministic job id keeps mutation assertions easy to trace when failures occur.
    result = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"url": "https://mutate.test"}],
        options={"job_id": "mutate-1"},
    )[0]

    assert result.status == ItemStatus.DONE
    assert result.extras == {"source": "hook"}
    assert result.timings == {"duration": 1.23}
