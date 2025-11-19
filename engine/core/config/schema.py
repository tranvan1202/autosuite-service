# root/engine/core/config/schema.py
"""Typed Settings schema loaded from environment with safe defaults."""
# Why: central place to see knobs, their types, and defaults.

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Immutable snapshot of runtime configuration."""

    api_key_enabled: bool = Field(default=False)
    api_key: str = Field(default="changeme")

    driver: Literal["playwright", "selenium"] = Field(default="playwright")
    pw_headless: bool = Field(default=True)
    pw_tracing: Literal["on", "off", "retain-on-failure"] = Field(default="retain-on-failure")
    pw_video: Literal["off", "retain-on-failure"] = Field(default="retain-on-failure")

    # Limits
    max_items_per_job: int = Field(default=200)
    payload_max_bytes: int = Field(default=512 * 1024)
    page_size_default: int = Field(default=50)
    page_size_max: int = Field(default=500)
    item_max_retries: int = Field(default=2)

    # Paths / artifacts
    artifacts_dir: str = Field(default="./var/artifacts")
    reports_dir: str = Field(default="./var/reports")
    artifacts_ttl_days: int = Field(default=7)

    # Locale
    display_tz: str = Field(default="Asia/Ho_Chi_Minh")

    # --- Service layer (added) ---
    db_url: str = "sqlite:///./var/app.db"
    db_echo: bool = False
    ui_poll_ms: int = 5000
    executor_max_workers: int = 1

    metrics_enabled: bool = Field(default=True)

    saucedemo_username: str = Field(default="")
    saucedemo_pw: str = Field(default="")
