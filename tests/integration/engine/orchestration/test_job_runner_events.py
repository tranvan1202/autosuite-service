# tests/integration/engine/orchestration/test_job_runner_events.py

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from engine.core.constants.flows import FlowType
from engine.orchestration import runner

pytestmark = pytest.mark.integration


class _InputModel(BaseModel):
    url: str


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
        self.spec = {"id": "events"}

    def run_item(self, input_obj: _InputModel, page: object) -> Any:
        return type(
            "_Result",
            (),
            {
                "ok": True,
                "value": {"url": input_obj.url},
                "error_code": None,
                "error_message": None,
                "timings": {"duration": 0.1},
                "extras": {},
            },
        )()


class _Logger:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **payload: Any) -> None:
        self.calls.append((event, payload))


@pytest.fixture
def event_capture(monkeypatch: pytest.MonkeyPatch) -> _Logger:
    logger = _Logger()
    monkeypatch.setattr(runner, "_logger", logger)
    return logger


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> _Adapter:
    adapter = _Adapter()

    def _get_adapter(flow: FlowType) -> _Adapter:
        return adapter

    monkeypatch.setattr(runner, "get_flow_adapter", _get_adapter)
    return adapter


def test_job_runner_emits_structured_events(
    adapter: _Adapter,
    configure_runner_settings,
    event_capture: _Logger,
) -> None:
    configure_runner_settings(0)

    # WHY: Dedicated job id makes event payload assertions deterministic.
    runner.run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=[{"url": "https://events.test"}],
        options={"job_id": "evt-1"},
    )

    evt_payloads = [payload for event, payload in event_capture.calls if event == "evt"]
    assert any(item.get("job_id") == "evt-1" for item in evt_payloads)
    assert any(item.get("item_index") == 0 for item in evt_payloads)
    assert any(item.get("status") is not None for item in evt_payloads)
