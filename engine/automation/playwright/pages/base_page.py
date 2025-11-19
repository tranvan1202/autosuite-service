# root/engine/automation/playwright/pages/base_page.py
"""Basic actions any flow can rely on."""
# Why: keep flows tiny; page code wraps Playwright specifics.

from __future__ import annotations

from typing import Any

from ....core.errors import FlowTimeoutError, NavigationError


class BasePage:
    """Thin wrapper around a Playwright Page."""

    def __init__(self, page: Any) -> None:
        self._page = page

    @property
    def page(self) -> Any:
        """Expose underlying Playwright page when flows need full power."""
        return self._page

    def safe_navigate(self, url: str) -> int | None:
        """Navigate once with sane defaults; raise typed errors for runner."""
        try:
            resp = self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return resp.status if resp else None
        except TimeoutError as e:
            raise FlowTimeoutError(str(e)) from e
        except Exception as e:
            raise NavigationError(str(e)) from e

    def collect_snapshot(self) -> dict[str, object]:
        """Capture minimal SEO-ish snapshot used by CRAWL_SIMPLE."""
        title = self._page.title()
        final_url = self._page.url
        # Meta tags: name/property → content
        meta_map = self._page.evaluate(
            """() => {
              const out = {};
              for (const el of document.querySelectorAll('meta')) {
                const k = el.getAttribute('name') || el.getAttribute('property');
                const v = el.getAttribute('content');
                if (k && v) out[k] = v;
              }
              return out;
            }"""
        )
        return {"title": title, "final_url": final_url, "meta_tags": meta_map}
