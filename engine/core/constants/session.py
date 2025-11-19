# root/engine/core/constants/session.py
"""Session spec enums used by registry/runner/session-factory."""
# Why: flows declare intent once; runner & session follow it.

from __future__ import annotations

from enum import StrEnum, unique


@unique
class SessionMode(StrEnum):
    """How we authorize the context upfront."""

    NON_AUTH = "NON_AUTH"
    COOKIES_AUTH = "COOKIES_AUTH"
    FORM_AUTH = "FORM_AUTH"


@unique
class ContextPer(StrEnum):
    """Lifecycle policy for BrowserContext."""

    JOB = "JOB"
    ITEM = "ITEM"
