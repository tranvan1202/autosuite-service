# tests/integration/engine/orchestration/test_job_runner_validation.py

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


class _AdapterHooks:
    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate_input(self, raw: dict[str, Any]) -> None:
        raise ValueError("url missing")

    def dedupe_key(self, raw: dict[str, Any]) -> str:
        return raw.get("url", "")

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        return None

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        return None

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        return None

    def after_job(self, ctx: dict[str, Any], summary: dict[str, int]) -> None:
        return None


class _Adapter:
    input_cls = _InputModel

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {"id": "validation"}

    def run_item(self, input_obj: _InputModel, page: object) -> Any:
        raise AssertionError("should not run when validation fails")


def test_validation_error_surfaces_in_results(monkeypatch, configure_runner_settings) -> None:
    configure_runner_settings(0)
    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)

    # WHY: Invalid payload deliberately misses `url` to exercise validation branch.
    result = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"wrong": "value"}],
        options={"job_id": "invalid-1"},
    )[0]

    assert result.status == ItemStatus.FAILED
    assert result.error_code == ErrorCode.UNKNOWN
    assert result.error_message == "url missing"
