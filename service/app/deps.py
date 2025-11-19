# root/service/app/deps.py
"""Common dependencies: settings, DB, templates, API-key guard."""
# Why: single place for engine/session wiring (API + workers).

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Annotated, cast

import structlog
from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from engine.core.config.loader import (
    get_settings as _get_settings,
    get_settings_fresh as _get_settings_fresh,
    reset_settings_cache as _reset_settings_cache,
)
from engine.core.config.schema import Settings
from service.constants.api import Header

_logger = structlog.get_logger(__name__)

# Jinja2 templates (register filters right after init)
templates = Jinja2Templates(directory="service/app/templates")

# DB engine/session (sync SQLAlchemy 2.x)
_ENGINE: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_engine() -> None:
    """Init global engine + session factory once at startup."""
    global _ENGINE, _SessionLocal
    if _ENGINE is not None and _SessionLocal is not None:
        return

    s = get_settings()
    # future=True cho SQLAlchemy 2.x style, echo controlled by env.
    _ENGINE = create_engine(s.db_url, echo=s.db_echo, future=True)
    _SessionLocal = sessionmaker(
        bind=_ENGINE,
        class_=Session,
        expire_on_commit=False,
    )


def get_session_factory() -> sessionmaker[Session] | None:
    """Expose session factory for workers/supervisor."""
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session per request."""
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized")

    factory = cast(sessionmaker[Session], _SessionLocal)
    db = factory()
    try:
        yield db
    finally:
        db.close()


async def close_db() -> None:
    """Dispose engine at shutdown (for uvicorn/reload)."""
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.dispose()
        _ENGINE = None


def init_logging() -> None:
    """Configure std logging early for uvicorn/structlog harmony."""
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_settings() -> Settings:
    """Expose engine settings to service layer."""
    return _get_settings()


def reset_settings_cache() -> None:
    """Tests/CI: force settings to refresh from current ENV."""
    _reset_settings_cache()


def get_settings_fresh() -> Settings:
    """Return a fresh Settings reloaded from ENV."""
    return _get_settings_fresh()


def init_jinja_filters() -> None:
    """Attach Jinja filters once."""
    try:
        from .utils.jinja_filters import (
            as_json,
            format_tz,
            nested_number_lines,
            short_text,
        )

        templates.env.filters["short_text"] = short_text
        templates.env.filters["as_json"] = as_json
        templates.env.filters["format_tz"] = format_tz
        templates.env.filters["nested_number_lines"] = nested_number_lines

        _logger.info("init_jinja_filters", message="success")
    except Exception as ex:
        _logger.error("error_init_jinja_filters", message=str(ex))


async def init_db() -> None:
    """Create engine and tables (SQLite file by default for Render Free)."""
    global _ENGINE, _SessionLocal
    if _ENGINE is not None and _SessionLocal is not None:
        return
    s = get_settings()
    _ENGINE = create_engine(s.db_url, echo=s.db_echo, pool_pre_ping=True, future=True)
    _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)

    # Auto-create tables for phase 1 (Alemic optional later)
    from service.db import models as m

    m.Base.metadata.create_all(_ENGINE)
    _logger.info("db_ready", url="db_ready")


# API key guard (optional via env)
_api_key_header = APIKeyHeader(name=Header.API_KEY, auto_error=False)


def require_api_key(
    key: Annotated[str | None, Depends(_api_key_header)],
    s: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Guard API when enabled; keep UI private for demo."""
    if not s.api_key_enabled:
        return
    if key and key == s.api_key:
        return
    raise HTTPException(status_code=401, detail="invalid_api_key")
