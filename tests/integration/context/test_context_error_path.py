# tests/integration/context/test_context_error_path.py

"""Integration test exercising error paths for tracing helpers."""
# WHY: Tracing failures must not cascade into flow crashes.

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.automation.playwright.session import policy

pytestmark = pytest.mark.integration


class _BrokenTracing:
    def start(self, **kwargs) -> None:
        raise RuntimeError("start failed")

    def stop(self, *, path: str) -> None:
        raise RuntimeError("stop failed")


def test_tracing_errors_are_swallowed(tmp_path: Path) -> None:
    context = SimpleNamespace(tracing=_BrokenTracing())
    out_path = tmp_path / "trace" / "broken.zip"

    policy.start_tracing(context)
    policy.stop_tracing(context, str(out_path))
