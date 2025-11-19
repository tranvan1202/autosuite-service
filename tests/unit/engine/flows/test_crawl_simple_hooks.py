# tests/unit/flows/test_crawl_simple_hooks.py
"""Unit tests for crawl_simple hooks validation and dedupe."""
# Why: keep flow contracts stable without touching Playwright.

from __future__ import annotations

import pytest

from engine.flows.crawl_simple import hooks as crawl_hooks


@pytest.mark.unit
def test_api_prevalidate_missing_url() -> None:
    """Missing url should be flagged by api_prevalidate."""
    items = [{"url": ""}]
    errors = crawl_hooks.api_prevalidate(items)
    assert len(errors) == 1
    assert errors[0]["code"] == "MISSING_URL"


@pytest.mark.unit
def test_api_prevalidate_invalid_scheme() -> None:
    """Non-http(s) urls should be rejected."""
    items = [{"url": "ftp://example.com"}]
    errors = crawl_hooks.api_prevalidate(items)
    assert len(errors) == 1
    assert errors[0]["code"] == "INVALID_SCHEME"


@pytest.mark.unit
def test_api_prevalidate_ok() -> None:
    """Valid urls should pass with no errors."""
    items = [{"url": "https://example.com"}, {"url": "http://example.com"}]
    errors = crawl_hooks.api_prevalidate(items)
    assert errors == []


@pytest.mark.unit
def test_validate_input_invalid_url_raises() -> None:
    """Strict validate_input must raise on invalid url."""
    with pytest.raises(ValueError, match="invalid_url"):
        crawl_hooks.validate_input({"url": "example.com"})


@pytest.mark.unit
def test_dedupe_key_stable() -> None:
    """dedupe_key should be deterministic for same input."""
    item = {"url": "https://example.com", "meta": {"raw_text": "Hello"}}
    k1 = crawl_hooks.dedupe_key(item)
    k2 = crawl_hooks.dedupe_key(item)
    assert k1 == k2
    assert "url=https://example.com" in k1
