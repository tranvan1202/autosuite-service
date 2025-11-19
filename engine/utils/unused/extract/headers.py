# root/engine/utils/extract/headers.py
"""Select and sanitize interesting response headers."""
# Why: logs and debug views need a safe, compact subset.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..jsonx import mask_headers

# Keep list short and generic; easy to extend later.
_WHITELIST = {
    "content-type",
    "content-length",
    "server",
    "cache-control",
    "expires",
    "pragma",
    "x-powered-by",
    "via",
}


def pick_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    """Return a masked, lower-cased subset of headers."""
    # Normalize keys to lowercase for stability across drivers.
    norm = {str(k).lower(): (str(v) if v is not None else "") for k, v in headers.items()}
    sel = {k: norm[k] for k in _WHITELIST if k in norm}
    return mask_headers(sel)
