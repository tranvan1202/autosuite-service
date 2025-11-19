# root/tests/integration/api/test_jobs_create_validation.py
"""API: surfacing validation errors from flow hooks."""
# Why: avoid bad jobs entering queue silently.

from __future__ import annotations

import pytest

from engine.core.constants.flows import FlowType


@pytest.mark.integration
@pytest.mark.api
def test_create_job_invalid_url_rejected(api_client, api_base) -> None:
    """Invalid url should return 422 with structured detail."""
    payload = {
        "flow_type": FlowType.CRAWL_SIMPLE.value,
        "items": [{"url": "not-a-url"}],
        "options": {},
    }

    resp = api_client.post(f"{api_base}/jobs", json=payload)
    body = resp.json()

    assert resp.status_code == 422
    assert "detail" in body
