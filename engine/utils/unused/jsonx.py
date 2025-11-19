# root/engine/utils/jsonx.py
"""JSON helpers with masking and stable dumps."""
# Why: keep logs safe and diffs stable across runs.

from __future__ import annotations

from typing import Any

import orjson

SENSITIVE_KEYS = {"password", "token", "authorization", "cookie", "secret", "api_key"}


def stable_dumps(obj: Any) -> str:
    """Deterministic JSON string for logs/artifacts."""
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS).decode("utf-8")


def mask_sensitive(d: dict[str, Any]) -> dict[str, Any]:
    """Mask values for known sensitive keys (shallow)."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if k.lower() in SENSITIVE_KEYS:
            out[k] = "***"
        else:
            out[k] = v
    return out


def mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    """Mask Authorization/Cookie-like headers."""
    out: dict[str, Any] = {}
    for k, v in headers.items():
        kn = k.lower()
        if "authorization" in kn or "cookie" in kn or kn in SENSITIVE_KEYS:
            out[k] = "***"
        else:
            out[k] = v
    return out
