# root/service/app/api/v1/metrics.py
"""Prometheus metrics endpoint."""
# Why: keep basic metrics available; extend later.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from engine.core.config.schema import Settings
from service.app.deps import get_settings, require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/metrics")
def metrics() -> Response:
    s: Settings = get_settings()

    if not s.metrics_enabled:
        raise HTTPException(status_code=404)

    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
