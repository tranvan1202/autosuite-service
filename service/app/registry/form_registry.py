# root/service/app/registry/form_registry.py
"""Form registry for flow UI (slug -> flow meta + normalizers)."""

# Why: single source of truth for FE forms without mixing JSON APIs.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from engine.core.constants.flows import FlowType

# Import Pydantic inputs from engine
from engine.flows.crawl_simple.input import CrawlSimpleInput
from engine.flows.flow_sauce_demo.input import SauceDemoInput


@dataclass(frozen=True, slots=True)
class FlowMeta:
    """FE-facing flow metadata used to render/normalize forms."""

    slug: str  # kebab-case used by UI/BDD
    enum_name: str  # engine enum string (for flow_type payload)
    input_cls: type[BaseModel]  # Pydantic v2 input model
    template_path: str  # Jinja template for the form
    normalize_fn: Callable[[dict[str, Any]], dict[str, Any]]  # FE form -> API: /jobs payload
    pretty_input_fn: Callable[[dict[str, Any]], str]  # used by jobs.py to render raw_text


# ---------- Pretty-text helpers ----------
def _pretty_crawl_simple(it: dict[str, Any]) -> str:
    return str(it.get("url") or "").strip()


def _pretty_sauce_demo(it: dict[str, Any]) -> str:
    fn = str(it.get("first_name") or "").strip()
    ln = str(it.get("last_name") or "").strip()
    pc = str(it.get("postal_code") or "").strip()
    names = it.get("product_names") or []
    if isinstance(names, list):
        names = [str(x).strip() for x in names if str(x).strip()]
    return f"{fn} {ln} ({pc}) — names: {', '.join(names)}"


# ---------- Normalizers (FE form -> BE payload) ----------
def _norm_crawl_simple(form: dict[str, Any]) -> dict[str, Any]:
    urls = [u.strip() for u in (form.get("urls") or "").splitlines() if u.strip()]
    return {
        "flow_type": FlowType.CRAWL_SIMPLE,
        "items": [{"url": u, "meta": {}} for u in urls],
        "options": {"dedupe": True},
    }


def _norm_sauce_demo(form: dict[str, Any]) -> dict[str, Any]:
    products = [s.strip() for s in (form.get("product_names") or "").split(",") if s.strip()]
    return {
        "flow_type": FlowType.FLOW_SAUCE_DEMO,
        "items": [
            {
                "first_name": (form.get("first_name") or "").strip(),
                "last_name": (form.get("last_name") or "").strip(),
                "postal_code": (form.get("postal_code") or "").strip(),
                "product_names": products,
                "meta": {},
            }
        ],
        "options": {"dedupe": True},
    }


# ---------- Master registry (keyed by slug) ----------
FLOW_REGISTRY: dict[str, FlowMeta] = {
    "crawl-simple": FlowMeta(
        slug="crawl-simple",
        enum_name=FlowType.CRAWL_SIMPLE,
        input_cls=CrawlSimpleInput,
        template_path="forms/crawl_simple.html",
        normalize_fn=_norm_crawl_simple,
        pretty_input_fn=_pretty_crawl_simple,
    ),
    "flow-sauce-demo": FlowMeta(
        slug="flow-sauce-demo",
        enum_name=FlowType.FLOW_SAUCE_DEMO,
        input_cls=SauceDemoInput,
        template_path="forms/flow_sauce_demo.html",
        normalize_fn=_norm_sauce_demo,
        pretty_input_fn=_pretty_sauce_demo,
    ),
}


# ---------- Helpers (for FE + API) ----------
def get_flow_by_slug(slug: str) -> FlowMeta:
    fm = FLOW_REGISTRY.get(slug)
    if not fm:
        raise KeyError("flow_not_found")
    return fm


def get_flow_by_enum_name(enum_name: str) -> FlowMeta:
    for fm in FLOW_REGISTRY.values():
        if fm.enum_name == enum_name:
            return fm
    raise KeyError("flow_not_found")


def normalize_to_payload(slug: str, form: dict[str, Any]) -> dict[str, Any]:
    return get_flow_by_slug(slug).normalize_fn(form)
