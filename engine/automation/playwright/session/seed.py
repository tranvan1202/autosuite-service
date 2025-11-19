# root/engine/automation/playwright/session/seed.py
"""Generate a realistic profile seed for a BrowserContext."""
# Why: stable session fingerprint lowers false positives in bot checks.

from __future__ import annotations

import random
from typing import Any

import structlog

_logger = structlog.get_logger(__name__)

# Keep tiny, extend later; consistent with locale/tz used in settings.
_UA_POOL: list[dict[str, Any]] = [
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "locale": "en-US",
        "tz": "Asia/Ho_Chi_Minh",
        "mobile": False,
        "dpr": 1.25,
    },
    {
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 390, "height": 844},
        "locale": "en-US",
        "tz": "Asia/Ho_Chi_Minh",
        "mobile": True,
        "dpr": 3.0,
    },
]


def make_seed(seed: int | None = None) -> dict[str, Any]:
    """Return a small profile dict for Playwright context options."""
    r = random.Random(seed)
    prof = r.choice(_UA_POOL)
    _logger.info(
        "session_seed_selected", ua=prof["ua"], viewport=prof["viewport"], mobile=prof["mobile"]
    )
    return prof.copy()
