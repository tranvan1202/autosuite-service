# root/engine/core/config/loader.py
"""ENV-first settings loader with early logging and secret masking."""
# Why: read ENV in one place, cache it, and make logs safe for CI artifacts.

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import structlog

from . import envkeys as EK
from .schema import Settings

_logger = structlog.get_logger(__name__)

# ---- dotenv bootstrap (load once at import)


def _discover_env_file() -> Path | None:
    """Find .env: prefer AUTOSUITE_ENV_FILE; else walk up to repo root."""
    override = os.getenv("AUTOSUITE_ENV_FILE")
    if override:
        p = Path(override).expanduser().resolve()
        return p if p.exists() else None
    # repo root heuristic: engine/core/config/loader.py -> root/
    root = Path(__file__).resolve().parents[3]
    env = root / ".env"
    return env if env.exists() else None


def _load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv
    except Exception as e:
        _logger.error("dotenv_error", path=str(e))
        return  # python-dotenv not installed? skip silently
    p = _discover_env_file()
    if p:
        # do not override existing process env by default
        load_dotenv(p, override=False)
        _logger.info("dotenv_loaded", path=str(p))
    else:
        _logger.debug("dotenv_not_found")


_load_dotenv_if_present()

# ---- helpers


def _coerce_bool(val: str | None, default: bool) -> bool:
    """Parse common truthy/falsey strings for ergonomics."""
    if val is None:
        return default
    v = val.strip().lower()
    return v in {"1", "true", "yes", "on"}


def _coerce_int(val: str | None, default: int) -> int:
    """Convert to int; tolerate blanks/whitespace."""
    if val is None:
        return default
    v = val.strip()
    if not v:
        return default
    try:
        return int(v)
    except Exception:
        _logger.error("env_int_parse_failed", value=v)
        return default


def _mask(s: str | None) -> str:
    """Hide secrets but keep length/context for debugging."""
    if not s:
        return ""
    if len(s) <= 4:
        return "****"
    return s[:2] + "…" + s[-2:]


def _mask_db_url(url: str) -> str:
    from urllib.parse import urlsplit, urlunsplit

    if not url:
        return ""
    parts = urlsplit(url)
    if not parts.username:
        return url
    # mask user/pass
    netloc = parts.hostname or ""
    if parts.port:
        netloc += f":{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


# ---- loader


@lru_cache(1)
def get_settings() -> Settings:
    """Load once; callers import this instead of os.getenv."""
    defaults = Settings().model_dump()

    data: dict[str, Any] = {
        "api_key_enabled": _coerce_bool(
            os.getenv(str(EK.API_KEY_ENABLED)), defaults["api_key_enabled"]
        ),
        "api_key": os.getenv(str(EK.API_KEY), defaults["api_key"]),
        "driver": os.getenv(str(EK.DRIVER), defaults["driver"]),
        "max_items_per_job": _coerce_int(
            os.getenv(str(EK.MAX_ITEMS_PER_JOB)), defaults["max_items_per_job"]
        ),
        "payload_max_bytes": _coerce_int(
            os.getenv(str(EK.PAYLOAD_MAX_BYTES)), defaults["payload_max_bytes"]
        ),
        "page_size_default": _coerce_int(
            os.getenv(str(EK.PAGE_SIZE_DEFAULT)), defaults["page_size_default"]
        ),
        "page_size_max": _coerce_int(os.getenv(str(EK.PAGE_SIZE_MAX)), defaults["page_size_max"]),
        "item_max_retries": _coerce_int(
            os.getenv(str(EK.ITEM_MAX_RETRIES)), defaults["item_max_retries"]
        ),
        "pw_headless": _coerce_bool(os.getenv(str(EK.PW_HEADLESS)), defaults["pw_headless"]),
        "pw_tracing": os.getenv(str(EK.PW_TRACING), defaults["pw_tracing"]),
        "pw_video": os.getenv(str(EK.PW_VIDEO), defaults["pw_video"]),
        "metrics_enabled": _coerce_bool(
            os.getenv(str(EK.METRICS_ENABLED)), defaults["metrics_enabled"]
        ),
        "artifacts_dir": os.getenv(str(EK.ARTIFACTS_DIR), defaults["artifacts_dir"]),
        "reports_dir": os.getenv(str(EK.REPORTS_DIR), defaults["reports_dir"]),
        "artifacts_ttl_days": _coerce_int(
            os.getenv(str(EK.ARTIFACTS_TTL_DAYS)), defaults["artifacts_ttl_days"]
        ),
        "display_tz": os.getenv(str(EK.DISPLAY_TZ), defaults["display_tz"]),
        # DB + service extras (make sure schema has these fields)
        "db_url": os.getenv(str(EK.DB_URL), defaults.get("db_url", "sqlite:///./var/app.db")),
        "db_echo": _coerce_bool(os.getenv(str(EK.DB_ECHO)), defaults.get("db_echo", False)),
        "ui_poll_ms": _coerce_int(os.getenv(str(EK.UI_POLL_MS)), defaults.get("ui_poll_ms", 5000)),
        "executor_max_workers": _coerce_int(
            os.getenv(str(EK.EXECUTOR_MAX_WORKERS)), defaults.get("executor_max_workers", 1)
        ),
        "saucedemo_username": os.getenv(str(EK.SAUCEDEMO_USERNAME), defaults["saucedemo_username"]),
        "saucedemo_pw": os.getenv(str(EK.SAUCEDEMO_PW), defaults["saucedemo_pw"]),
    }

    settings = Settings(**data)

    # Early structured log so misconfig is visible in CI
    _logger.info(
        "settings_loaded",
        driver=settings.driver,
        api_key_enabled=settings.api_key_enabled,
        api_key=_mask(settings.api_key),
        db_url=_mask_db_url(settings.db_url),
        limits=dict(
            max_items_per_job=settings.max_items_per_job,
            payload_max_bytes=settings.payload_max_bytes,
            page_size_default=settings.page_size_default,
            page_size_max=settings.page_size_max,
            item_max_retries=settings.item_max_retries,
        ),
        pw=dict(
            headless=settings.pw_headless, tracing=settings.pw_tracing, video=settings.pw_video
        ),
        paths=dict(artifacts=settings.artifacts_dir, reports=settings.reports_dir),
        metrics_enabled=settings.metrics_enabled,
        display_tz=settings.display_tz,
        ui_poll_ms=getattr(settings, "ui_poll_ms", None),
        executor_max_workers=getattr(settings, "executor_max_workers", None),
    )
    return settings


# -------- NEW: testing/CI helpers --------


def reset_settings_cache() -> None:
    """Clear cached Settings snapshot to re-read ENV on next call."""
    try:
        get_settings.cache_clear()
    except Exception as e:
        # Safeguard: never break tests if functools internals change.
        _logger.error("reset_settings_cache_failed", err=str(e))


def get_settings_fresh() -> Settings:
    """Force re-load Settings from ENV (used by tests/CI to assert new values)."""
    reset_settings_cache()
    return get_settings()
