# tests/integration/engine/orchestration/test_job_runner_dedupe_toggle.py
from __future__ import annotations

from collections import deque
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
    def __init__(self, ok: bool, value: dict[str, Any] | None) -> None:
        self.ok = ok
        self.value = value
        self.error_code = ErrorCode.NONE
        self.error_message = None
        self.timings = {"duration": 0.2}
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
        return None

    def after_job(self, ctx: dict[str, Any], summary: dict[str, int]) -> None:
        return None


class _Adapter:
    input_cls = _InputModel

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.spec = {"id": "toggle"}
        self._responses = deque(
            [
                _Result(ok=True, value={"url": "https://example.com"}),
                _Result(ok=True, value={"url": "https://example.com"}),
                _Result(ok=True, value={"url": "https://example.com"}),
            ]
        )
        self.run_item_calls = 0

    def run_item(self, input_obj: _InputModel, page: object) -> _Result:
        self.run_item_calls += 1
        return self._responses.popleft()


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> _Adapter:
    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)
    return adapter


def test_run_job_honors_dedupe_toggle(adapter: _Adapter, configure_runner_settings) -> None:
    configure_runner_settings(0)

    items = [
        # WHY: Duplicate payload exercises dedupe toggle wiring.
        {"url": "https://duplicate.test"},
        {"url": "https://duplicate.test"},
        {"url": "https://duplicate.test"},
    ]
    results = runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=items,
        options={"job_id": "dedupe-off", "dedupe": False},
    )

    assert [r.status for r in results] == [
        ItemStatus.DONE,
        ItemStatus.DONE,
        ItemStatus.DONE,
    ]
    assert adapter.run_item_calls == 3
