# root/service/app/api/v1/flows.py
"""Flow registry endpoints (read-only for FE tooling)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from service.app.deps import require_api_key
from service.app.registry.form_registry import (
    FLOW_REGISTRY,
    get_flow_by_slug,
)

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("")
def list_flows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for fm in FLOW_REGISTRY.values():
        out.append({"slug": fm.slug, "flow_type": fm.enum_name, "template_path": fm.template_path})
    return out


@router.get("/{slug}/input-spec")
def input_spec(slug: str) -> dict[str, Any]:
    try:
        fm = get_flow_by_slug(slug)
    except KeyError as err:
        raise HTTPException(status_code=404, detail="flow_not_found") from err

    fields = []
    for name, f in fm.input_cls.model_fields.items():
        fields.append(
            {
                "name": name,
                "required": f.is_required(),
                "annotation": str(f.annotation),
                "default": None if f.default is None else f.default,
                "json_schema": f.json_schema_extra or {},
            }
        )
    return {"slug": fm.slug, "flow_type": fm.enum_name, "fields": fields}
