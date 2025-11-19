# root/service/app/validation.py
"""API-side pre-validation wired to flow adapters.
Why: avoid duplicating rules; flows own their validation contract.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import structlog

from engine.core.constants.flows import FlowType
from engine.flows.registry import get_flow_adapter

_logger = structlog.get_logger(__name__)

ValidationError = dict[str, Any]  # {"idx": int, "code": str, "message": str}


def _call_api_prevalidate(hooks: Any, items: list[dict[str, Any]]) -> list[ValidationError]:
    """Call hooks.api_prevalidate(items) if present; must be pure & cheap."""
    fn: Callable | None = getattr(hooks, "api_prevalidate", None)
    if not callable(fn):
        return []
    try:
        out = fn(items)
        # normalize
        results: list[ValidationError] = []
        for e in out or []:
            idx = int(e.get("idx", 0))
            code = str(e.get("code", "INVALID_INPUT"))
            msg = str(e.get("message", "invalid input"))
            results.append({"idx": idx, "code": code, "message": msg})
        return results
    except Exception as e:
        # Do not blow up API if a flow mis-implements api_prevalidate.
        return [{"idx": -1, "code": "PREVALIDATE_ERROR", "message": str(e)}]


def _pydantic_validate(adapter: Any, items: Iterable[dict[str, Any]]) -> list[ValidationError]:
    """Use the flow's input_cls to catch schema/type errors early."""
    errs: list[ValidationError] = []
    input_cls = getattr(adapter, "input_cls", None)
    if input_cls is None:
        return errs
    for i, raw in enumerate(items):
        try:
            # minimal fields only; keep meta passthrough
            input_cls(**{"url": raw.get("url"), "meta": raw.get("meta") or {}})
        except Exception as e:
            errs.append({"idx": i, "code": "SCHEMA_ERROR", "message": str(e)})
    return errs


def prevalidate(flow: FlowType, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a list of {"idx","code","message"}; empty list means OK.

    Very important: do NOT instantiate input_cls here. Only the flow's
    api_prevalidate() should run, because runner will do deep validation later.
    """
    try:
        adapter = get_flow_adapter(flow)
    except Exception as e:
        # turn into 422-like contract used by /jobs
        return [{"idx": -1, "code": "FLOW_NOT_SUPPORTED", "message": str(e)}]

    fn = getattr(adapter.hooks, "api_prevalidate", None)
    if not callable(fn):
        return []

    try:
        errs = fn(items) or []
        # normalize structure a bit
        norm: list[dict[str, Any]] = []
        for i, err in enumerate(errs):
            norm.append(
                {
                    "idx": int(err.get("idx", i)),
                    "code": str(err.get("code", "INVALID")),
                    "message": str(err.get("message", ""))[:500],
                }
            )
        return norm
    except Exception as e:
        # never explode the /jobs call
        _logger.warning("api_prevalidate_raised", flow=str(flow), err=str(e))
        return [{"idx": -1, "code": "PREVALIDATE_EXCEPTION", "message": str(e)}]
