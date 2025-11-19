# root/engine/automation/playwright/session/injectors.py
"""Load/merge secrets and inject into a Playwright context or page."""
# Why: flows pass secret names; we resolve to files safely and merge.

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import structlog

_logger = structlog.get_logger(__name__)

# Resolve secrets root (overrideable via ENV for deploys)
_DEFAULT_ROOT = Path(__file__).resolve().parents[4] / "secrets"
_SECRETS_ROOT = Path(os.getenv("AUTOSUITE_SECRETS_DIR", str(_DEFAULT_ROOT)))

# Allow dot/underscore/dash to keep short names; block traversal.
_SAFE_NAME = re.compile(r"^[a-zA-Z0-9._\-]+$")


def _safe(name: str) -> str:
    """Reject path tricks; only allow simple filenames."""
    if not name or not _SAFE_NAME.match(name):
        raise ValueError("invalid_secret_name")
    return name


def _read_json(path: Path) -> Any:
    """Small helper that fails loud and early."""
    with path.open("r", encoding="utf8") as fh:
        return json.load(fh)


def _cookie_paths(names: Iterable[str]) -> list[Path]:
    """Map names to cookie file paths under secrets/cookies/."""
    base = _SECRETS_ROOT / "cookies"
    return [base / f"{_safe(n)}.json" for n in names]


def _form_paths(names: Iterable[str]) -> list[Path]:
    """Map names to form-auth file paths under secrets/form_auth/."""
    base = _SECRETS_ROOT / "form_auth"
    return [base / f"{_safe(n)}.json" for n in names]


def load_cookie_files(names: Iterable[str]) -> list[dict[str, Any]]:
    """Read and merge cookie JSON arrays from multiple names."""
    merged: list[dict[str, Any]] = []
    paths = _cookie_paths(names)
    for p in paths:
        if not p.exists():
            _logger.info("cookie_file_missing", path=str(p))
            continue
        data = _read_json(p)
        if isinstance(data, list):
            merged.extend(data)
        else:
            _logger.warning("cookie_file_not_list", path=str(p))
    # Deduplicate by (name, domain, path) keeping last occurrence
    dedup: dict[tuple[str | None, str | None, str], dict[str, Any]] = {}
    for c in merged:
        key = (c.get("name"), c.get("domain"), c.get("path", "/"))
        dedup[key] = c
    final = list(dedup.values())
    _logger.info("cookies_merged", count=len(final), files=[str(p) for p in paths])
    return final


def load_form_auth_files(names: Iterable[str]) -> dict[str, Any]:
    """Merge form_auth JSON objects from multiple names (last wins)."""
    creds: dict[str, Any] = {}
    paths = _form_paths(names)
    for p in paths:
        if not p.exists():
            _logger.info("form_auth_file_missing", path=str(p))
            continue
        data = _read_json(p)
        if isinstance(data, dict):
            creds.update(data)
        else:
            _logger.warning("form_auth_not_object", path=str(p))
    _logger.info("form_auth_merged", keys=sorted(creds.keys()), files=[str(p) for p in paths])
    return creds


def inject_cookies(context: Any, *names: str) -> None:
    """Resolve names → cookies and inject into context."""
    cookies = load_cookie_files(names)
    if not cookies:
        return
    try:
        context.add_cookies(cookies)
        _logger.info("cookies_injected", count=len(cookies))
    except Exception as exc:  # pragma: no cover
        _logger.warning("cookies_inject_failed", err=str(exc), count=len(cookies))


def get_form_auth(*names: str) -> dict[str, Any]:
    """Return merged credentials for flows to use as they see fit."""
    return load_form_auth_files(names)
