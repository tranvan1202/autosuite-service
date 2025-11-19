# tests/integration/context/test_context_tracing.py

"""Integration test covering tracing helpers with session bundle."""
# WHY: Tracing toggles must cooperate with factory bundles for observability.

from __future__ import annotations

from pathlib import Path

import pytest

from engine.automation.playwright.session import context_factory, policy
from engine.automation.playwright.session.context_factory import FlowSessionSpec
from engine.core.constants.session import SessionMode

pytestmark = pytest.mark.integration


class _TracingSpy:
    def __init__(self) -> None:
        self.started: list[dict[str, object]] = []
        self.stopped: list[str] = []

    def start(self, **kwargs) -> None:
        self.started.append(kwargs)

    def stop(self, *, path: str) -> None:
        self.stopped.append(path)


def test_start_stop_tracing_with_bundle(fake_playwright, tmp_path: Path) -> None:
    bundle = context_factory.build_session_bundle(
        headless=True,
        spec=FlowSessionSpec(mode=SessionMode.NON_AUTH, secret_names=[], page_reuse=False),
    )
    tracer = _TracingSpy()
    bundle.context.tracing = tracer  # type: ignore[assignment]

    out_path = tmp_path / "trace" / "flow" / "job" / "item.zip"

    policy.start_tracing(bundle.context)
    policy.stop_tracing(bundle.context, str(out_path))

    assert tracer.started == [{"screenshots": True, "snapshots": True, "sources": False}]
    assert tracer.stopped == [str(out_path)]
    assert out_path.parent.exists()
