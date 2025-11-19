# root/tests/unit/engine/flows/crawl_simple/test_hooks_validation.py
from __future__ import annotations

import pytest

from engine.flows.crawl_simple import hooks


@pytest.mark.unit
@pytest.mark.parametrize(
    "item, expected_codes",
    [
        (
            {},  # thiếu URL
            {"MISSING_URL"},
        ),
        (
            {"url": ""},
            {"MISSING_URL"},
        ),
        (
            {"url": "ftp://example.com"},
            {"INVALID_SCHEME"},
        ),
        (
            {"url": "http://example.com"},
            set(),
        ),
        (
            {"url": "https://example.com"},
            set(),
        ),
    ],
)
def test_api_prevalidate_crawl_simple(item, expected_codes):
    errors = hooks.api_prevalidate([item])
    codes = {e["code"] for e in errors}
    assert codes == expected_codes


@pytest.mark.unit
@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com/path?q=1",
    ],
)
def test_validate_input_ok(url):
    hooks.validate_input({"url": url})


@pytest.mark.unit
@pytest.mark.parametrize(
    "url, expected_message",
    [
        ("", "invalid_url"),
        ("  ", "invalid_url"),
        ("ftp://example.com", "invalid_url"),
    ],
)
def test_validate_input_invalid(url, expected_message):
    with pytest.raises(ValueError, match=expected_message) as excinfo:
        hooks.validate_input({"url": url})
    assert str(excinfo.value) == expected_message


@pytest.mark.unit
def test_dedupe_key_uses_normalized_url_and_raw_text():
    item = {
        "url": "HTTPS://Example.COM/path",
        "meta": {"raw_text": "  Hello World  "},
    }
    key = hooks.dedupe_key(item)
    # thể hiện ta hiểu normalize logic: lower + trim
    assert "https://example.com/path" in key
    assert "hello world" in key
