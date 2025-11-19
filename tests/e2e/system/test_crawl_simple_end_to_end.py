# root/tests/e2e/system/test_crawl_simple_end_to_end.py
"""System E2E: CRAWL_SIMPLE via HTTP API."""
# Why: black-box verification of service + engine wiring.

from __future__ import annotations

import pytest

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus


@pytest.mark.e2e
@pytest.mark.regression
def test_crawl_simple_end_to_end(system_client, api_base) -> None:
    """Creating a job should yield items with final status."""
    payload = {
        "flow_type": FlowType.CRAWL_SIMPLE.value,
        "items": [{"url": "https://example.com"}],
        "options": {},
    }

    resp = system_client.post(f"{api_base}/jobs", json=payload)
    body = resp.json()
    job_id = body["job_id"]

    items_resp = system_client.get(f"{api_base}/jobs/{job_id}/items")
    items = items_resp.json()["items"]

    assert resp.status_code == 201
    assert len(items) == 1
    assert items[0]["status"] in (ItemStatus.DONE, ItemStatus.FAILED, ItemStatus.CANCELLED)
