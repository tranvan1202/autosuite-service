# tests/integration/flows/conftest.py

"""Fixtures for flow adapter integration tests."""
# WHY: Flow integrations rely on Playwright; fixtures stub configs per suite.

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def flow_settings(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    settings = SimpleNamespace(pw_headless=True, pw_tracing="off")
    monkeypatch.setattr("engine.flows.crawl_simple.run.get_settings", lambda: settings)
    monkeypatch.setattr("engine.flows.crawl_simple.hooks.get_settings", lambda: settings)
    monkeypatch.setattr("engine.flows.flow_sauce_demo.hooks.get_settings", lambda: settings)
    return settings
