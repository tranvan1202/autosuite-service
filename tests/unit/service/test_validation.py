# root/tests/unit/service/app/test_validation.py
from __future__ import annotations

from typing import Any

import pytest

from engine.core.constants.flows import FlowType
from service.app import validation


@pytest.mark.unit
def test_call_api_prevalidate_no_hook_returns_empty() -> None:
    """_call_api_prevalidate returns [] when hooks has no api_prevalidate."""

    class Hooks:
        pass

    items: list[dict[str, Any]] = [{"url": "https://example.com"}]
    out = validation._call_api_prevalidate(Hooks(), items)
    assert out == []


@pytest.mark.unit
def test_call_api_prevalidate_normalizes_output() -> None:
    """_call_api_prevalidate normalizes idx/code/message with defaults."""

    class Hooks:
        def api_prevalidate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return [
                {"idx": "1", "code": "ERR", "message": "bad"},
                {"code": "NO_IDX"},  # missing idx
                {},  # missing code/message
            ]

    items: list[dict[str, Any]] = [{"url": "u1"}, {"url": "u2"}, {"url": "u3"}]
    out = validation._call_api_prevalidate(Hooks(), items)

    assert len(out) == 3
    assert out[0]["idx"] == 1
    assert out[0]["code"] == "ERR"
    assert out[0]["message"] == "bad"

    assert isinstance(out[1]["idx"], int)
    assert out[1]["code"] == "NO_IDX"

    assert isinstance(out[2]["idx"], int)
    assert out[2]["code"] == "INVALID_INPUT"
    assert out[2]["message"] == "invalid input"


@pytest.mark.unit
def test_call_api_prevalidate_handles_exceptions() -> None:
    """_call_api_prevalidate wraps hook exceptions as PREVALIDATE_ERROR."""

    class Hooks:
        def api_prevalidate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            raise RuntimeError("boom")

    out = validation._call_api_prevalidate(Hooks(), [{"url": "x"}])
    assert len(out) == 1
    err = out[0]
    assert err["idx"] == -1
    assert err["code"] == "PREVALIDATE_ERROR"
    assert "boom" in err["message"]


@pytest.mark.unit
def test_pydantic_validate_ok_when_input_cls_accepts_data() -> None:
    """_pydantic_validate returns [] when input_cls accepts payload."""

    class FakeInput:
        def __init__(self, url: str | None, meta: dict[str, Any]) -> None:
            self.url = url
            self.meta = meta

    class Adapter:
        input_cls = FakeInput

    items: list[dict[str, Any]] = [{"url": "https://example.com", "meta": {"k": "v"}}]
    out = validation._pydantic_validate(Adapter(), items)
    assert out == []


@pytest.mark.unit
def test_pydantic_validate_collects_schema_errors() -> None:
    """_pydantic_validate collects SCHEMA_ERROR when constructor raises."""

    class FakeInput:
        def __init__(self, url: str | None, meta: dict[str, Any]) -> None:
            msg = f"bad:{url}"
            raise ValueError(msg)

    class Adapter:
        input_cls = FakeInput

    items: list[dict[str, Any]] = [{"url": "x", "meta": {}}, {"url": "y"}]
    out = validation._pydantic_validate(Adapter(), items)

    assert len(out) == 2
    first = out[0]
    assert first["idx"] == 0
    assert first["code"] == "SCHEMA_ERROR"
    assert "bad:x" in first["message"]


@pytest.mark.unit
def test_prevalidate_flow_not_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """prevalidate returns FLOW_NOT_SUPPORTED when registry lookup fails."""

    def fake_get_flow_adapter(flow: FlowType) -> Any:
        raise RuntimeError("unsupported")

    monkeypatch.setattr(validation, "get_flow_adapter", fake_get_flow_adapter)

    items: list[dict[str, Any]] = [{"url": "https://example.com"}]
    out = validation.prevalidate(FlowType.CRAWL_SIMPLE, items)

    assert len(out) == 1
    err = out[0]
    assert err["idx"] == -1
    assert err["code"] == "FLOW_NOT_SUPPORTED"
    assert "unsupported" in err["message"]


@pytest.mark.unit
def test_prevalidate_no_api_prevalidate_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """prevalidate returns [] when adapter.hooks has no api_prevalidate."""

    class Hooks:
        pass

    class Adapter:
        def __init__(self) -> None:
            self.hooks = Hooks()

    def fake_get_flow_adapter(flow: FlowType) -> Any:
        return Adapter()

    monkeypatch.setattr(validation, "get_flow_adapter", fake_get_flow_adapter)

    out = validation.prevalidate(FlowType.CRAWL_SIMPLE, [{"url": "https://example.com"}])
    assert out == []


@pytest.mark.unit
def test_prevalidate_normalizes_errors_from_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    """prevalidate normalizes idx/code/message and caps message length."""

    class Hooks:
        def api_prevalidate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            long_msg = "x" * 600
            return [
                {"idx": "5", "code": "BAD", "message": "oops"},
                {"code": "NO_IDX"},
                {"message": long_msg},
            ]

    class Adapter:
        def __init__(self) -> None:
            self.hooks = Hooks()

    def fake_get_flow_adapter(flow: FlowType) -> Any:
        return Adapter()

    monkeypatch.setattr(validation, "get_flow_adapter", fake_get_flow_adapter)

    out = validation.prevalidate(
        FlowType.CRAWL_SIMPLE, [{"url": "u1"}, {"url": "u2"}, {"url": "u3"}]
    )

    assert len(out) == 3
    assert out[0]["idx"] == 5
    assert out[0]["code"] == "BAD"
    assert out[0]["message"] == "oops"

    assert isinstance(out[1]["idx"], int)
    assert out[1]["code"] == "NO_IDX"

    assert isinstance(out[2]["idx"], int)
    assert out[2]["code"] == "INVALID"
    assert len(out[2]["message"]) == 500


@pytest.mark.unit
def test_prevalidate_wraps_hook_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """prevalidate turns hook exception into PREVALIDATE_EXCEPTION error."""

    class Hooks:
        def api_prevalidate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            raise RuntimeError("boom-hook")

    class Adapter:
        def __init__(self) -> None:
            self.hooks = Hooks()

    def fake_get_flow_adapter(flow: FlowType) -> Any:
        return Adapter()

    monkeypatch.setattr(validation, "get_flow_adapter", fake_get_flow_adapter)

    out = validation.prevalidate(FlowType.CRAWL_SIMPLE, [{"url": "https://example.com"}])
    assert len(out) == 1
    err = out[0]
    assert err["idx"] == -1
    assert err["code"] == "PREVALIDATE_EXCEPTION"
    assert "boom-hook" in err["message"]
