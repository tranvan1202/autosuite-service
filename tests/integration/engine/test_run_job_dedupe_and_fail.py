# root/tests/integration/engine/test_run_job_dedupe_and_fail.py
"""run_job integration for dedupe + failure behavior."""
# Why: demonstrate runner decisions independent of HTTP/UI.

from __future__ import annotations

import pytest

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.orchestration.runner import run_job


@pytest.mark.integration
def test_run_job_dedupe_and_failures(patch_mixed_adapter) -> None:
    """Duplicates should be cancelled; bad items should fail."""
    items = [
        {"url": "https://example.com"},
        {"url": "https://example.com"},  # duplicate
        {"url": "https://fail.example.com"},  # adapter-level failure
    ]

    results = run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=items,
        options={"job_id": "job-int-2"},
    )

    assert results[0].status == ItemStatus.DONE
    assert results[1].status == ItemStatus.CANCELLED
    assert results[2].status == ItemStatus.FAILED
