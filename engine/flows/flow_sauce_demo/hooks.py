# root/engine/flows/flow_sauce_demo/hooks.py
"""Hooks for FLOW_SAUCE_DEMO."""
# Why: keep validation/dedupe/session near the flow.

from __future__ import annotations

import os
import re
from typing import Any, cast

import structlog

from engine.automation.playwright.session.context_factory import SessionBundle
from engine.core.config.loader import get_settings

_logger = structlog.get_logger(__name__)

_NAME = re.compile(r"^[\w\s\-.\']{1,50}$", re.UNICODE)
_POSTAL = re.compile(r"^[A-Za-z0-9\-\s]{3,12}$")

FlowCtx = dict[str, Any]


def field_options() -> dict[str, list[str]]:
    """Provide FE suggestions for product names."""
    return {
        "product_names": [
            "Sauce Labs Backpack",
            "Sauce Labs Bike Light",
            "Sauce Labs Bolt T-Shirt",
            "Sauce Labs Fleece Jacket",
            "Sauce Labs Onesie",
            "Test.allTheThings() T-Shirt (Red)",
        ]
    }


def api_prevalidate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cheap pre-DB validation."""
    errors: list[dict[str, Any]] = []
    for i, it in enumerate(items):
        fn = (it or {}).get("first_name", "").strip()
        ln = (it or {}).get("last_name", "").strip()
        pc = (it or {}).get("postal_code", "").strip()
        names = (it or {}).get("product_names") or []
        if not fn or not ln or not pc:
            errors.append(
                {"idx": i, "code": "MISSING_REQUIRED", "message": "first/last/postal required"}
            )
        if not names or len(names) < 1:
            errors.append(
                {"idx": i, "code": "NO_PRODUCTS", "message": "product_names must have ≥1"}
            )
    return errors


def validate_input(item_input: dict[str, Any]) -> None:
    """Runner-side strict validation."""
    fn = str(item_input.get("first_name") or "").strip()
    ln = str(item_input.get("last_name") or "").strip()
    pc = str(item_input.get("postal_code") or "").strip()
    names = item_input.get("product_names") or []
    if not (_NAME.match(fn) and _NAME.match(ln)):
        raise ValueError("invalid_name")
    if not _POSTAL.match(pc):
        raise ValueError("invalid_postal_code")
    if not isinstance(names, list) or not names:
        raise ValueError("invalid_product_names")
    if len(names) > 10:
        raise ValueError("too_many_products")


def before_job(context: dict[str, Any]) -> FlowCtx:
    """Create job-level context to avoid cold-start per item."""
    s = get_settings()
    spec = context["spec"]
    ctx: FlowCtx = {"bundle": None, "page": None, "page_reuse": False, "__trace_path__": None}
    if getattr(spec, "context_per", "JOB") == "JOB":
        from engine.automation.playwright.session import build_session_bundle

        ctx["bundle"] = build_session_bundle(headless=s.pw_headless, spec=spec, seed_value=None)
    ctx["page_reuse"] = getattr(spec, "page_reuse", False)
    _logger.info("hook_before_job", headless=s.pw_headless, reuse=ctx["page_reuse"])
    return ctx


def before_item(ctx: FlowCtx, item_input: dict[str, Any]) -> Any:
    """Return a ready page; glue for POM chain."""
    from engine.automation.playwright.session import ensure_page, policy as _pol

    s = get_settings()

    bundle = ctx.get("bundle")
    if bundle is None:
        raise RuntimeError("Session bundle not initialized in before_job")
    sb = cast(SessionBundle, bundle)

    page = ensure_page(sb, reuse=ctx.get("page_reuse", False))
    ctx["page"] = page

    if str(s.pw_tracing).lower() in ("on", "1", "true"):
        job_id = ((item_input.get("meta") or {}).get("job_id")) or "job"
        idx = ((item_input.get("meta") or {}).get("idx")) or 0
        flow = ((item_input.get("meta") or {}).get("flow_type")) or "FLOW"
        base = os.getenv("AUTOSUITE_ARTIFACTS_DIR", "./var/artifacts")
        trace_path = os.path.join(base, "trace", str(flow), str(job_id), f"item-{idx}.zip")
        ctx["__trace_path__"] = trace_path
        _pol.start_tracing(ctx["bundle"].context)

    _logger.debug("hook_before_item")
    return page


def after_item(ctx: FlowCtx, item_result: dict[str, Any]) -> None:
    """Close page if not reusing."""
    from engine.automation.playwright.session import policy as _pol

    try:
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
    """Close bundle at end of job."""
    if ctx.get("bundle"):
        from engine.automation.playwright.session import close_bundle

        close_bundle(ctx["bundle"])
        ctx["bundle"] = None
    _logger.info("hook_after_job", **summary)


def on_retry(item_input: dict[str, Any], attempt: int, error: Exception) -> None:
    _logger.warning("hook_on_retry", attempt=attempt, err=str(error))


def on_error(item_input: dict[str, Any], error: Exception) -> None:
    _logger.error("hook_on_error", err=str(error))


def dedupe_key(item: dict[str, Any]) -> str:
    """Stable key: 4 input fields."""
    fn = (item.get("first_name") or "").strip().lower()
    ln = (item.get("last_name") or "").strip().lower()
    pc = (item.get("postal_code") or "").strip().lower()
    names = "|".join(sorted((n or "").strip().lower() for n in (item.get("product_names") or [])))
    return f"fn={fn}|ln={ln}|pc={pc}|names={names}"
