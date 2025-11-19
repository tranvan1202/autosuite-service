# root/service/app/main.py
"""FastAPI app with lifespan, routers, and Jinja2/HTMX pages."""
# Why: clean split between JSON API and HTML views.

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles

from ..constants.api import API_TITLE, API_V1_PREFIX, API_VERSION
from ..executor.scheduler import reconcile_stale_jobs, schedule_jobs
from .api.v1 import api_v1
from .deps import (
    close_db,
    get_session_factory,
    get_settings,
    init_db,
    init_jinja_filters,
    init_logging,
)
from .views import pages as pages_views, partials as partials_views

s = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Init logging + DB; keep startup predictable on Render."""
    init_logging()
    init_jinja_filters()
    # app.state.db = await init_db() # type: ignore[attr-defined]
    await init_db()

    # Reconcile stale RUNNING jobs from previous crash.
    factory = get_session_factory()
    if factory is not None:
        db = factory()
        try:
            reconcile_stale_jobs(db)
            schedule_jobs(db)
        except Exception:
            import structlog

            structlog.get_logger().exception("startup.reconcile_or_schedule_failed")
        finally:
            db.close()

    yield
    await close_db()


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
    middleware=[
        Middleware(GZipMiddleware),
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
        # Dev: ["*"]; Prod: ["published-domain.com", "*.onrender.com"]
        Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
    ],
)

# JSON API (versioned)
app.include_router(api_v1, prefix=API_V1_PREFIX)

# HTML Views (no /api prefix)
app.include_router(pages_views.router)
app.include_router(partials_views.router)

BASE_DIR = Path(__file__).resolve().parent

# Prefer AUTOSUITE_STATIC_DIR; if not present, use default ./static
STATIC_DIR = Path(os.getenv("AUTOSUITE_STATIC_DIR", BASE_DIR / "static"))

# Make sure the directory exists (local, CI, Published site)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR), check_dir=False),
    name="static",
)

# app.mount("/static", StaticFiles(directory="service/app/static"), name="static")
