# root/tests/integration/api/test_jobs_idempotency_and_limits.py
"""API: idempotency + payload size limits for job creation."""
# Why: ensure /jobs is safe against retries & oversized payloads.

from __future__ import annotations

import pytest

from engine.core.constants.flows import FlowType
from service.constants.api import Header as APIHeader


@pytest.mark.integration
@pytest.mark.api
def test_create_job_is_idempotent_for_same_key(api_client, api_base) -> None:
    """Same Idempotency-Key + payload should reuse the same job_id."""
    payload = {
        "flow_type": FlowType.CRAWL_SIMPLE.value,
        "items": [{"url": "https://example.com"}],
        "options": {},
    }
    headers = {APIHeader.IDEMPOTENCY_KEY.value: "demo-idempotent-key-1"}

    first_resp = api_client.post(f"{api_base}/jobs", json=payload, headers=headers)
    first_body = first_resp.json()

    second_resp = api_client.post(f"{api_base}/jobs", json=payload, headers=headers)
    second_body = second_resp.json()

    assert first_resp.status_code == 201
    assert second_resp.status_code == 201
    assert "job_id" in first_body
    assert "job_id" in second_body
    assert first_body["job_id"] == second_body["job_id"]
    assert first_body["items_count"] == 1
    assert second_body["items_count"] == 1


@pytest.mark.integration
@pytest.mark.api
def test_create_job_rejects_payload_too_large(api_client, api_base) -> None:
    """Payload larger than payload_max_bytes should return 413."""
    # Default payload_max_bytes = 512 * 1024, so create string > 600_000 bytes to be sure.
    big_text = "x" * 600_000

    payload = {
        "flow_type": FlowType.CRAWL_SIMPLE.value,
        "items": [
            {
                "url": "https://example.com",
                "note": big_text,
            }
        ],
        "options": {},
    }

    resp = api_client.post(f"{api_base}/jobs", json=payload)
    body = resp.json()

    assert resp.status_code == 413
    assert body["detail"] == "payload_too_large"
