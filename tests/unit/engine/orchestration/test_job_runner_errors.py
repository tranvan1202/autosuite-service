# tests/unit/engine/orchestration/test_job_runner_errors.py

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.core.errors import ErrorCode
from engine.orchestration import runner


class _InputModel(BaseModel):
    url: str


class _DomainError(Exception):
    code = ErrorCode.INVALID_INPUT


# WHY: Collect adapter error callbacks to verify custom exception mapping.
class _AdapterHooks:
    def __init__(self) -> None:
        self.on_error_calls: list[Exception] = []

    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate_input(self, raw: dict[str, Any]) -> None:
        return None

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        return None

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        self.on_error_calls.append(exc)

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        return None

    def after_job(self, ctx: dict[str, Any], summary: dict[str, Any]) -> None:
        return None


class _Adapter:
    input_cls = _InputModel

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {}

    def run_item(self, input_obj: _InputModel, page: object) -> Any:
        raise _DomainError("bad input")


pytestmark = pytest.mark.unit


def test_run_job_maps_exceptions_and_calls_on_error(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(0)

    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    results = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"url": "https://example.com"}],
        options={"job_id": "job-err"},
    )

    assert len(results) == 1
    result = results[0]
    assert result.status == ItemStatus.FAILED
    assert result.error_code == ErrorCode.INVALID_INPUT
    assert result.error_message == "bad input"
    assert adapter.hooks.on_error_calls
    assert isinstance(adapter.hooks.on_error_calls[0], _DomainError)
