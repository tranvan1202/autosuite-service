# tests/unit/engine/orchestration/test_job_runner_inputs.py

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from engine.orchestration.runner import _materialize_input


class _InputModel(BaseModel):
    url: str
    note: str | None = None


class _Adapter:
    input_cls = _InputModel


pytestmark = pytest.mark.unit


def test_materialize_input_filters_unknown_fields() -> None:
    adapter = _Adapter()
    raw = {"url": "https://example.com", "note": None, "ignored": "value"}

    result = _materialize_input(raw, adapter)

    assert result.url == "https://example.com"
    assert result.note is None
    assert not hasattr(result, "ignored")


def test_materialize_input_requires_declared_fields() -> None:
    adapter = _Adapter()

    with pytest.raises(ValidationError) as excinfo:
        _materialize_input({"ignored": "value"}, adapter)

    assert "url" in str(excinfo.value)
