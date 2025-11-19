# root/tests/helpers/settings.py
"""Helpers to patch ENV and get fresh Settings in tests."""
# Why: tests flip ENV per-case; we must refresh settings snapshot.

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from service.app.deps import get_settings_fresh, reset_settings_cache


@contextmanager
def patched_settings(**env) -> Iterator:
    """Temporarily set ENV, refresh Settings, and restore after."""
    prev = {k: os.environ.get(k) for k in env}
    try:
        os.environ.update({k: str(v) for k, v in env.items()})
        reset_settings_cache()
        yield get_settings_fresh()
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        reset_settings_cache()
