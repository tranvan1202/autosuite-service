# tests/integration/engine/orchestration/test_job_runner_summary.py

from __future__ import annotations

from collections import deque
from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.core.errors import ErrorCode
from engine.orchestration import runner


class _InputModel(BaseModel):
    url: str


class _Result:
    def __init__(
        self,
        ok: bool,
        value: dict[str, Any] | None,
        error_code: ErrorCode,
        error_message: str | None,
    ) -> None:
        self.ok = ok
        self.value = value
        self.error_code = error_code
        self.error_message = error_message
        self.timings = {"duration": 0.3}
        self.extras: dict[str, Any] = {}


# WHY: Mirror adapter contract to observe summary aggregation across retries and dedupe paths.
class _AdapterHooks:
    def __init__(self) -> None:
        self.after_job_summary: dict[str, int] | None = None
        self.after_item_payloads: list[dict[str, Any]] = []
        self.retry_calls: list[int] = []

    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate_input(self, raw: dict[str, Any]) -> None:
        return None

    def dedupe_key(self, raw: dict[str, Any]) -> str:
        return raw["url"]

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        self.retry_calls.append(attempt)

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        return None

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        payload.setdefault("extras", {})["hook"] = True
        self.after_item_payloads.append(dict(payload))

    def after_job(self, ctx: dict[str, Any], summary: dict[str, int]) -> None:
        self.after_job_summary = dict(summary)


class _Adapter:
    input_cls = _InputModel

    def __init__(self, responses: deque[_Result]) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {"id": "demo"}
        self._responses = responses
        self.run_item_calls = 0

    def run_item(self, input_obj: _InputModel, page: object) -> _Result:
        self.run_item_calls += 1
        return self._responses.popleft()


pytestmark = pytest.mark.integration


def test_job_runner_summarizes_mixed_outcomes(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(0)

    # WHY: Blend successful, failed, and deduped responses to exercise summary rollup.
    responses = deque(
        [
            _Result(ok=True, value={"url": "a"}, error_code=ErrorCode.NONE, error_message=None),
            _Result(ok=False, value=None, error_code=ErrorCode.UNKNOWN, error_message="fail"),
        ]
    )
    adapter = _Adapter(responses)

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    results = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"url": "a"}, {"url": "b"}, {"url": "a"}],
        options={"job_id": "mix"},
    )

    assert [r.status for r in results] == [
        ItemStatus.DONE,
        ItemStatus.FAILED,
        ItemStatus.CANCELLED,
    ]
    assert results[0].extras == {"hook": True}
    assert results[1].error_message == "fail"
    assert adapter.run_item_calls == 2
    assert adapter.hooks.after_job_summary == {"done": 1, "failed": 1, "cancelled": 1}
    assert adapter.hooks.retry_calls == []
