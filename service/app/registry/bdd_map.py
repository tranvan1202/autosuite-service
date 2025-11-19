# root/service/app/registry/bdd_map.py
"""Role → flow registry used by the home/dashboard pages."""
# Why: simple catalog so non-technical users can discover flows by role.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BDDFeature:
    role: str
    role_slug: str
    project: str
    feature: str
    flow_slug: str  # e.g. "flow-sauce-demo", "crawl-simple"


# Seed entries for demo; extend freely.
BDD_ENTRIES: list[BDDFeature] = [
    BDDFeature(
        role="Manual Tester",
        role_slug="manual-tester",
        project="SauceDemo",
        feature="Checkout E2E",
        flow_slug="flow-sauce-demo",
    ),
    BDDFeature(
        role="SEO Analyst",
        role_slug="seo-analyst",
        project="Generic",
        feature="Crawl page title/meta",
        flow_slug="crawl-simple",
    ),
]
