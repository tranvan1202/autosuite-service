# root/engine/flows/crawl_simple/hooks.py
"""Lifecycle hooks for CRAWL_SIMPLE."""
# Why: predictable hook points help observability and extension.

from __future__ import annotations

import os
from typing import Any, cast

import structlog

from engine.automation.playwright.session.context_factory import SessionBundle

from ...core.config.envkeys import ARTIFACTS_DIR
from ...core.config.loader import get_settings

_logger = structlog.get_logger(__name__)

FlowCtx = dict[str, Any]


def before_job(context: dict[str, Any]) -> FlowCtx:
    """Create job-level context to avoid cold-start per item."""
    s = get_settings()
    spec = context["spec"]
    ctx: FlowCtx = {"bundle": None, "page": None, "page_reuse": False, "__trace_path__": None}
    if getattr(spec, "context_per", "JOB") == "JOB":
        from engine.automation.playwright.session import build_session_bundle

        ctx["bundle"] = build_session_bundle(
            headless=s.pw_headless,
            spec=spec,
            seed_value=None,
        )

    ctx["page_reuse"] = getattr(spec, "page_reuse", False)
    _logger.info("hook_before_job", headless=s.pw_headless, reuse=ctx["page_reuse"])
    return ctx


def before_item(ctx: FlowCtx, item_input: dict[str, Any]) -> Any:
    """Return a ready page for this item; flow decides reuse/new page; optionally start tracing."""
    from engine.automation.playwright.session import ensure_page, policy as _pol

    s = get_settings()
    bundle = ctx.get("bundle")
    if bundle is None:
        # If the spec allows per-ITEM, it can be built here; for simplicity, raise explicitly:
        raise RuntimeError("Session bundle not initialized in before_job")
    sb = cast(SessionBundle, bundle)

    page = ensure_page(sb, reuse=ctx.get("page_reuse", False))
    ctx["page"] = page

    # Start tracing per item if enabled
    if str(s.pw_tracing).lower() in ("on", "1", "true"):
        job_id = ((item_input.get("meta") or {}).get("job_id")) or "job"
        idx = ((item_input.get("meta") or {}).get("idx")) or 0
        flow = ((item_input.get("meta") or {}).get("flow_type")) or "FLOW"
        base = os.getenv(ARTIFACTS_DIR, "./var/artifacts")
        trace_path = os.path.join(base, "trace", str(flow), str(job_id), f"item-{idx}.zip")
        ctx["__trace_path__"] = trace_path
        _pol.start_tracing(ctx["bundle"].context)

    _logger.debug("hook_before_item", url=item_input.get("url"))
    return page


def after_item(ctx: FlowCtx, item_result: dict[str, Any]) -> None:
    """Stop tracing (if any) and optionally close page."""
    from engine.automation.playwright.session import policy as _pol

    try:
        # Stop trace and record path
        trace_path = ctx.get("__trace_path__")
        if trace_path and ctx.get("bundle"):
            _pol.stop_tracing(ctx["bundle"].context, trace_path)
            item_result.setdefault("extras", {})
            item_result["extras"]["trace_path"] = trace_path

        p = ctx.get("page")
        if p and not ctx.get("page_reuse"):
            p.close()
    except Exception as e:
        _logger.error("hook_after_item_failed", err=str(e))
    finally:
        ctx["page"] = None
        ctx["__trace_path__"] = None
        _logger.debug("hook_after_item", status=item_result.get("status"))


def after_job(ctx: FlowCtx, summary: dict[str, Any]) -> None:
    """Tear down job-level resources."""
    if ctx.get("bundle"):
        from engine.automation.playwright.session import close_bundle

        close_bundle(ctx["bundle"])
        ctx["bundle"] = None
    _logger.info("hook_after_job", **summary)


def api_prevalidate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cheap pre-DB validation for API /jobs."""
    errors: list[dict[str, Any]] = []
    for i, it in enumerate(items):
        url = (it or {}).get("url") or ""
        if not url:
            errors.append({"idx": i, "code": "MISSING_URL", "message": "url is required"})
        elif not (url.startswith("http://") or url.startswith("https://")):
            errors.append(
                {"idx": i, "code": "INVALID_SCHEME", "message": "url must start with http(s)"}
            )
    return errors


def validate_input(item_input: dict[str, Any]) -> None:
    """Runner-side strict validation."""
    url = str(item_input.get("url") or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("invalid_url")


def on_retry(item_input: dict[str, Any], attempt: int, error: Exception) -> None:
    _logger.warning("hook_on_retry", attempt=attempt, err=str(error), url=item_input.get("url"))


def on_error(item_input: dict[str, Any], error: Exception) -> None:
    _logger.error("hook_on_error", err=str(error), url=item_input.get("url"))


def dedupe_key(item: dict[str, Any]) -> str:
    """Stable key: normalized url + raw_text hint."""
    url = (item.get("url") or "").strip().lower()
    meta = item.get("meta") or {}
    raw = (meta.get("raw_text") or "").strip().lower()
    return f"url={url}|raw={raw}"
