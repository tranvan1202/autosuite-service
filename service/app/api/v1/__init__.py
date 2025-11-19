# root/service/app/api/v1/init.py
"""API v1 aggregator."""
# Why: single include point keeps main.py clean.

from __future__ import annotations

from fastapi import APIRouter

from . import flows, health, history, jobs, metrics

api_v1 = APIRouter()
api_v1.include_router(health.router, tags=["health"])
api_v1.include_router(metrics.router, tags=["metrics"])
api_v1.include_router(flows.router, prefix="/flows", tags=["flows"])
api_v1.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1.include_router(history.router, prefix="/history", tags=["history"])
