# root/engine/orchestration/runner.py
"""Sequential runner using FlowAdapter + hooks."""
# Why: keep orchestration boring; flows own session/page details.

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import structlog

from ..core.config.loader import get_settings
from ..core.constants.flows import FlowType
from ..core.constants.statuses import ItemStatus, JobStatus
from ..core.errors import ErrorCode, to_error_code
from ..core.models.item_result import ItemResult
from ..flows.registry import get_flow_adapter
from .events import ItemFinished, ItemStarted, JobFinished, JobStarted

_logger = structlog.get_logger(__name__)


def _fallback_dedupe_key(item: dict[str, Any]) -> str:
    """Fallback key based on URL + meta; deterministic and cheap."""
    url = (item.get("url") or "").strip().lower()
    meta = item.get("meta") or {}
    parts = [url] + [f"{k}={meta[k]}" for k in sorted(meta)]
    return "|".join(parts)


def _materialize_input(raw: dict[str, Any], adapter: Any) -> Any:
    """Build flow input model using declared Pydantic fields."""
    fields = getattr(adapter.input_cls, "model_fields", {})

    # payload = {k: raw.get(k) for k in fields.keys() if k in raw}
    # Get common keys and build payload
    common_keys = fields.keys() & raw.keys()
    payload = {k: raw[k] for k in common_keys}

    return adapter.input_cls(**payload)


def run_job(
    flow: FlowType, items: list[dict[str, Any]], options: dict[str, Any]
) -> list[ItemResult]:
    """Sequential job runner; no threading, no signals, just hooks + retries."""
    settings = get_settings()
    adapter = get_flow_adapter(flow)

    job_id = str(options.get("job_id") or "n/a")

    _logger.info("run_job_enter", flow=str(flow), items=len(items))
    _logger.info("evt", **asdict(JobStarted(job_id=job_id, flow=flow)))

    results: list[ItemResult] = []
    seen_keys: set[str] = set()
    dedupe_on = bool(options.get("dedupe", True))

    # Job-level context managed by flow (browser/session policy).
    hook_ctx = adapter.hooks.before_job(
        {
            "flow": str(flow),
            "options": options,
            "spec": adapter.spec,
        }
    )
    hook_ctx["page_reuse"] = getattr(adapter, "page_reuse", False)

    try:
        for idx, raw in enumerate(items):
            # ---- validate input ----
            try:
                adapter.hooks.validate_input(raw)
            except Exception as exc:
                # Hard fail this item, continue others.
                results.append(
                    ItemResult(
                        status=ItemStatus.FAILED,
                        error_code=to_error_code(exc),
                        error_message=str(exc),
                    )
                )
                adapter.hooks.after_item(hook_ctx, {"status": ItemStatus.FAILED})
                continue

            # ---- dedupe ----
            key = ""
            if dedupe_on:
                if hasattr(adapter.hooks, "dedupe_key"):
                    try:
                        key = adapter.hooks.dedupe_key(raw) or ""
                    except Exception:
                        key = _fallback_dedupe_key(raw)
                else:
                    key = _fallback_dedupe_key(raw)

                if key and key in seen_keys:
                    results.append(
                        ItemResult(
                            status=ItemStatus.CANCELLED,
                            error_code=ErrorCode.DEDUPED,
                            error_message=ErrorCode.DEDUPED,
                        )
                    )
                    adapter.hooks.after_item(hook_ctx, {"status": ItemStatus.CANCELLED})
                    continue

                if key:
                    seen_keys.add(key)

            _logger.info(
                "evt",
                **asdict(
                    ItemStarted(
                        job_id=job_id,
                        item_index=idx,
                    )
                ),
            )

            # ---- page lifecycle driven by flow hooks ----
            page = adapter.hooks.before_item(hook_ctx, raw)
            attempts = int(settings.item_max_retries) + 1
            final_result: ItemResult | None = None

            for attempt in range(attempts):
                try:
                    input_obj = _materialize_input(raw, adapter)
                    ar = adapter.run_item(input_obj, page)

                    if ar.ok and ar.value is not None:
                        final_result = ItemResult(
                            status=ItemStatus.DONE,
                            retry_count=attempt,
                            error_code=ErrorCode.NONE,
                            output=ar.value,
                            timings=ar.timings,
                            extras=ar.extras or {},
                        )
                        break

                    # Retry on soft failure.
                    if attempt < attempts - 1:
                        msg = ar.error_message or str(ar.error_code)
                        adapter.hooks.on_retry(raw, attempt + 1, RuntimeError(msg))
                        continue

                    # Out of retries -> failed.
                    final_result = ItemResult(
                        status=ItemStatus.FAILED,
                        retry_count=attempt,
                        error_code=ar.error_code,
                        error_message=ar.error_message,
                        timings=ar.timings,
                        extras=ar.extras or {},
                    )

                except Exception as exc:
                    code = to_error_code(exc)
                    if attempt < attempts - 1:
                        adapter.hooks.on_retry(raw, attempt + 1, exc)
                        continue
                    adapter.hooks.on_error(raw, exc)
                    final_result = ItemResult(
                        status=ItemStatus.FAILED,
                        error_code=code,
                        error_message=str(exc),
                    )

            results.append(
                final_result
                or ItemResult(
                    status=ItemStatus.FAILED,
                    error_code=ErrorCode.UNKNOWN,
                    error_message="no_result",
                )
            )
            _last = results[-1]
            mutable_view: dict[str, Any] = {
                "status": _last.status,
                "timings": dict(_last.timings or {}),
                "extras": dict(_last.extras or {}),
            }
            adapter.hooks.after_item(hook_ctx, mutable_view)
            _last.timings = mutable_view.get("timings") or _last.timings
            _last.extras = mutable_view.get("extras") or _last.extras

            _logger.info(
                "evt",
                **asdict(
                    ItemFinished(
                        job_id=job_id,
                        item_index=idx,
                        status=results[-1].status,
                    )
                ),
            )

        # ---- summary ----
        summary = {
            "done": sum(1 for r in results if r.status == ItemStatus.DONE),
            "failed": sum(1 for r in results if r.status == ItemStatus.FAILED),
            "cancelled": sum(1 for r in results if r.status == ItemStatus.CANCELLED),
        }
        adapter.hooks.after_job(hook_ctx, summary)

        if summary["cancelled"] > 0 and (summary["done"] + summary["failed"]) < len(results):
            job_status = JobStatus.CANCELLED
        elif summary["failed"] > 0:
            job_status = JobStatus.FAILED
        else:
            job_status = JobStatus.DONE

        _logger.info("evt", **asdict(JobFinished(job_id=job_id, flow=flow, status=job_status)))
        _logger.info("run_job_leave", **summary)
    finally:
        # Flow hooks own cleanup; runner stays boring.
        pass

    return results
