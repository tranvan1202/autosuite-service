# root/engine/automation/playwright/pages/common_page.py
"""High-level actions composed from BasePage."""
# Why: flows call one method instead of wiring steps each time.

from __future__ import annotations

from .base_page import BasePage


class CommonPage(BasePage):
    """Expose a compact surface for crawl/validate flows."""

    def navigate_and_collect(self, url: str) -> dict[str, object]:
        """Go to url and return {title, final_url, http_status, meta_tags}."""
        status = self.safe_navigate(url)
        snap = self.collect_snapshot()
        snap["http_status"] = status
        return snap
