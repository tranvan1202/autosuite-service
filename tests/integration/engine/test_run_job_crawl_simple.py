# root/tests/integration/engine/test_run_job_crawl_simple.py
"""run_job integration with all-ok fake adapter."""
# Why: prove happy-path orchestration without browser/HTTP.

from __future__ import annotations

import pytest

from engine.core.constants.flows import FlowType
from engine.core.constants.statuses import ItemStatus
from engine.orchestration.runner import run_job


@pytest.mark.integration
@pytest.mark.regression
def test_run_job_single_item_done(patch_all_ok_adapter) -> None:
    """Single valid item should complete as DONE."""
    items = [{"url": "https://example.com"}]

    results = run_job(
        flow=FlowType.CRAWL_SIMPLE,
        items=items,
        options={"job_id": "job-int-1"},
    )

    assert len(results) == 1
    assert results[0].status == ItemStatus.DONE

    actual_output = results[0].output
    assert actual_output["final_url"] == "https://example.com/"
    assert actual_output["http_status"] == 200
    assert actual_output["title"] == "Example Domain"
