# root/engine/core/config/envkeys.py
"""Canonical environment variable names. Prevents string typos spreading."""
from typing import Final

# Why: one source of truth for ENV names makes refactors safe and grep-able.

API_KEY_ENABLED: Final[str] = "AUTOSUITE_API_KEY_ENABLED"
API_KEY: Final[str] = "AUTOSUITE_API_KEY"

DRIVER: Final[str] = "AUTOSUITE_DRIVER"  # playwright | selenium (default: playwright)

MAX_ITEMS_PER_JOB: Final[str] = "AUTOSUITE_MAX_ITEMS_PER_JOB"
PAYLOAD_MAX_BYTES: Final[str] = "AUTOSUITE_PAYLOAD_MAX_BYTES"
PAGE_SIZE_DEFAULT: Final[str] = "AUTOSUITE_PAGE_SIZE_DEFAULT"
PAGE_SIZE_MAX: Final[str] = "AUTOSUITE_PAGE_SIZE_MAX"

PW_HEADLESS: Final[str] = "AUTOSUITE_PW_HEADLESS"
PW_TRACING: Final[str] = "AUTOSUITE_PW_TRACING"  # on | off | retain-on-failure
PW_VIDEO: Final[str] = "AUTOSUITE_PW_VIDEO"  # off | retain-on-failure

METRICS_ENABLED: Final[str] = "AUTOSUITE_METRICS_ENABLED"

ARTIFACTS_DIR: Final[str] = "AUTOSUITE_ARTIFACTS_DIR"
REPORTS_DIR: Final[str] = "AUTOSUITE_REPORTS_DIR"
ARTIFACTS_TTL_DAYS: Final[str] = "AUTOSUITE_ARTIFACTS_TTL_DAYS"

ITEM_MAX_RETRIES: Final[str] = "AUTOSUITE_ITEM_MAX_RETRIES"

DISPLAY_TZ: Final[str] = "AUTOSUITE_DISPLAY_TZ"

DB_URL: Final[str] = "AUTOSUITE_DB_URL"
DB_ECHO: Final[str] = "AUTOSUITE_DB_ECHO"
UI_POLL_MS: Final[str] = "AUTOSUITE_UI_POLL_MS"
EXECUTOR_MAX_WORKERS: Final[str] = "AUTOSUITE_EXECUTOR_MAX_WORKERS"

SAUCEDEMO_USERNAME: Final[str] = "SAUCEDEMO_USERNAME"
SAUCEDEMO_PW: Final[str] = "SAUCEDEMO_PW"
