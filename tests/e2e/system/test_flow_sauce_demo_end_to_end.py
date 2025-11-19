# root/tests/e2e/system/test_flow_sauce_demo_end_to_end.py
"""System E2E: FLOW_SAUCE_DEMO via HTTP API with Playwright tracing enabled."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from engine.core.config.envkeys import PW_TRACING
from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus


@pytest.mark.e2e
@pytest.mark.ui_playwright
def test_sauce_demo_flow_end_to_end(system_client: TestClient, monkeypatch, api_base) -> None:
    """Create FLOW_SAUCE_DEMO job; expect DONE and trace artifact path recorded in extras."""
    # Enable tracing only for this test (artifacts dir is already ./var/artifacts)
    from service.app.deps import get_settings_fresh, reset_settings_cache

    monkeypatch.setenv(PW_TRACING, "on")
    reset_settings_cache()
    s = get_settings_fresh()
    assert s.pw_tracing == "on"

    payload = {
        "flow_type": FlowType.FLOW_SAUCE_DEMO.value,
        "items": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "postal_code": "70000",
                "product_names": ["Sauce Labs Backpack"],
            }
        ],
        "options": {},
    }

    resp = system_client.post(f"{api_base}/jobs", json=payload)
    body = resp.json()
    job_id = body["job_id"]

    items_resp = system_client.get(f"{api_base}/jobs/{job_id}/items")
    items = items_resp.json()["items"]

    assert resp.status_code == 201
    assert len(items) == 1
    assert items[0]["status"] == ItemStatus.DONE.value
    # Expect trace_path inside extras (hooks+runner write it when tracing=on)
    assert "trace_path" in (items[0]["extras"] or {})
