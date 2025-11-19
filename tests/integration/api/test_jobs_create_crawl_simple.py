# root/tests/integration/api/test_jobs_create_crawl_simple.py
"""API: create CRAWL_SIMPLE job."""
# Why: verify public contract for core entrypoint.

from __future__ import annotations

import pytest

from engine.core.constants.flows import FlowType


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.smoke
def test_create_crawl_simple_job_ok(api_client, api_base) -> None:
    """Valid payload should yield job_id and item count."""
    payload = {
        "flow_type": FlowType.CRAWL_SIMPLE.value,
        "items": [{"url": "https://example.com"}],
        "options": {},
    }

    resp = api_client.post(f"{api_base}/jobs", json=payload)
    body = resp.json()

    assert resp.status_code == 201
    assert "job_id" in body
    assert body["items_count"] == 1
