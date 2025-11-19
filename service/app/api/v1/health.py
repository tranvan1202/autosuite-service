# root/service/app/api/v1/health.py
# """Health endpoints."""
# Why: basic probes for Render/CI.

from __future__ import annotations

from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness for infra."""
    return {"status": "ok"}


@router.get("/livez")
def livez() -> Response:
    """Tiny head-friendly probe."""
    return Response(status_code=204)
