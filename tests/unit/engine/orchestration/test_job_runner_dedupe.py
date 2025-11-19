# tests/unit/engine/orchestration/test_job_runner_dedupe.py

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


class _ActionResult:
    def __init__(self, ok: bool, value: Any | None = None) -> None:
        self.ok = ok
        self.value = value
        self.error_code = ErrorCode.NONE
        self.error_message = None
        self.timings: dict[str, float] | None = None
        self.extras: dict[str, Any] | None = None


# WHY: Capture dedupe fallbacks and lifecycle payloads without invoking real adapter hooks.
class _AdapterHooks:
    def __init__(self) -> None:
        self.dedupe_calls = 0
        self.after_item_payloads: list[dict[str, Any]] = []

    def before_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate_input(self, raw: dict[str, Any]) -> None:
        return None

    def dedupe_key(self, raw: dict[str, Any]) -> str:
        self.dedupe_calls += 1
        raise RuntimeError("dedupe boom")

    def before_item(self, ctx: dict[str, Any], raw: dict[str, Any]) -> object:
        return object()

    def on_retry(self, raw: dict[str, Any], attempt: int, exc: Exception) -> None:
        return None

    def on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        return None

    def after_item(self, ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        self.after_item_payloads.append(payload)

    def after_job(self, ctx: dict[str, Any], summary: dict[str, Any]) -> None:
        return None


class _Adapter:
    input_cls = _InputModel
    hooks: _AdapterHooks
    spec = {"name": "dummy"}

    def __init__(self) -> None:
        self.hooks = _AdapterHooks()
        self.run_item_calls = 0

    def run_item(self, input_obj: _InputModel, page: object) -> _ActionResult:
        self.run_item_calls += 1
        return _ActionResult(ok=True, value={"url": input_obj.url})


pytestmark = pytest.mark.unit


def test_run_job_uses_fallback_when_dedupe_hook_errors(monkeypatch, configure_runner_settings):
    configure_runner_settings(0)

    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    fallback_calls: list[str] = []
    original_fallback = runner._fallback_dedupe_key

    def _fallback(raw: dict[str, Any]) -> str:
        key = original_fallback(raw)
        fallback_calls.append(key)
        return key

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)
    monkeypatch.setattr(runner, "_fallback_dedupe_key", _fallback)

    items = [{"url": "https://example.com"}, {"url": "https://example.com"}]
    results = runner.run_job(flow=FlowType.CRAWL_SIMPLE, items=items, options={"job_id": "J-1"})

    assert len(results) == 2
    assert results[0].status == ItemStatus.DONE
    assert results[1].status == ItemStatus.CANCELLED
    assert results[1].error_code == ErrorCode.DEDUPED
    assert adapter.run_item_calls == 1
    assert fallback_calls
    assert adapter.hooks.dedupe_calls == 2
    assert adapter.hooks.after_item_payloads[-1]["status"] == ItemStatus.CANCELLED
