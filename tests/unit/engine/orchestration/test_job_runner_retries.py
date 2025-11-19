# tests/unit/engine/orchestration/test_job_runner_retries.py

from __future__ import annotations

from collections import deque
from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.core.errors import ErrorCode
from engine.orchestration import runner


# WHY: Track retry/error callbacks to assert retry orchestration decisions.
class _AdapterHooks:
    def __init__(self) -> None:
        self.retry_calls: list[tuple[dict[str, Any], int]] = []
        self.error_calls: list[Exception] = []

    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate_input(self, raw: dict[str, Any]) -> None:
        return None

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        self.retry_calls.append((raw, attempt))

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        self.error_calls.append(exc)

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        return None

    def after_job(self, ctx: dict[str, Any], summary: dict[str, Any]) -> None:
        return None


class _InputModel(BaseModel):
    url: str


class _Adapter:
    def __init__(self, responses: deque[Any]) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {}
        self.input_cls = _InputModel
        self._responses = responses

    def run_item(self, input_obj: Any, page: object) -> Any:
        return self._responses.popleft()


class _Response:
    def __init__(self, ok: bool, error_code: ErrorCode, error_message: str) -> None:
        self.ok = ok
        self.value = None
        self.error_code = error_code
        self.error_message = error_message
        self.timings: dict[str, float] | None = {"duration": 0.5}
        self.extras: dict[str, Any] | None = {}


pytestmark = pytest.mark.unit


def test_run_job_retries_until_exhausted(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(1)

    responses: deque[_Response] = deque(
        [
            _Response(ok=False, error_code=ErrorCode.TIMEOUT, error_message="retry me"),
            _Response(ok=False, error_code=ErrorCode.UNKNOWN, error_message="still bad"),
        ]
    )
    adapter = _Adapter(responses)

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    results = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"url": "https://example.com"}],
        options={"job_id": "job-123"},
    )

    assert len(results) == 1
    result = results[0]
    assert result.status == ItemStatus.FAILED
    assert result.retry_count == 1
    assert result.error_code == ErrorCode.UNKNOWN
    assert result.error_message == "still bad"
    assert result.timings == {"duration": 0.5}
    assert result.extras == {}
    assert adapter.hooks.retry_calls == [({"url": "https://example.com"}, 1)]
    assert adapter.hooks.error_calls == []
    assert not responses
