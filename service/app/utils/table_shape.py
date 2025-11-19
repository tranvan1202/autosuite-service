# root/service/app/utils/table_shape.py
from __future__ import annotations

from typing import Any

_BASE_ORDER = ["status", "timings"]  # timings near status; others conditional


def _collect_domain_keys(rows: list[dict[str, Any]]) -> list[str]:
    keys: set[str] = set()
    for r in rows[:20]:
        v = r.get("output") or {}
        if isinstance(v, dict):
            keys.update(map(str, v.keys()))
    return sorted(keys)


def _has_asserted(rows: list[dict[str, Any]]) -> bool:
    for r in rows:
        ex = r.get("extras") or {}
        if isinstance(ex, dict) and isinstance(ex.get("asserted"), dict):
            return True
    return False


def _any_failed_or_cancelled(rows: list[dict[str, Any]]) -> bool:
    return any(r.get("status") in ("FAILED", "CANCELLED") for r in rows)


def _shape_row(r: dict[str, Any], domain_keys: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "status": r.get("status"),
    }
    t = r.get("timings") or {}
    out["timings"] = {"total": (t or {}).get("total")} if isinstance(t, dict) else None

    # optional diagnostics
    out["retry_count"] = r.get("retry_count")
    out["error_code"] = r.get("error_code")
    out["error_message"] = r.get("error_message")

    v = r.get("output") or {}
    if isinstance(v, dict):
        for k in domain_keys:
            out[k] = v.get(k)

    ex = r.get("extras") or {}
    if isinstance(ex, dict) and isinstance(ex.get("asserted"), dict):
        out["asserted"] = ex["asserted"]
    return out


def build_table(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    domain = _collect_domain_keys(rows)
    shaped = [_shape_row(r, domain) for r in rows]

    cols: list[str] = list(_BASE_ORDER)
    # show diagnostics only when needed
    if _any_failed_or_cancelled(rows):
        cols.extend(["retry_count", "error_code", "error_message"])
    cols.extend(domain)
    if _has_asserted(rows):
        cols.append("asserted")
    return cols, shaped
