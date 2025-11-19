# tests/unit/context/test_context_injectors.py

"""Unit tests for Playwright secret injectors."""
# WHY: Secret loaders feed flows; faking JSON keeps CI deterministic.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.automation.playwright.session import injectors

pytestmark = pytest.mark.unit


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf8")


def test_load_cookie_files_merges_and_dedupes(secrets_root: Path) -> None:
    first = secrets_root / "cookies" / "demo.json"
    second = secrets_root / "cookies" / "demo_extra.json"
    _write_json(first, [{"name": "sid", "domain": "example.com", "path": "/"}])
    _write_json(
        second,
        [
            {"name": "sid", "domain": "example.com", "path": "/"},
            {"name": "lang", "domain": "example.com", "path": "/"},
        ],
    )

    cookies = injectors.load_cookie_files(["demo", "demo_extra"])

    assert cookies == [
        {"name": "sid", "domain": "example.com", "path": "/"},
        {"name": "lang", "domain": "example.com", "path": "/"},
    ]


def test_load_form_auth_files_merges_dicts(secrets_root: Path) -> None:
    first = secrets_root / "form_auth" / "sauce_demo.json"
    second = secrets_root / "form_auth" / "fallback.json"
    # WHY: Mirror Sauce Demo credential keys used by flows.
    _write_json(first, {"username": "standard_user", "password": "secret_sauce"})
    _write_json(second, {"otp": "000000"})

    creds = injectors.load_form_auth_files(["fallback", "sauce_demo"])

    assert creds["username"] == "standard_user"
    assert creds["password"] == "secret_sauce"  # noqa: S105
    assert creds["otp"] == "000000"


def test_inject_cookies_noop_when_no_files(
    monkeypatch: pytest.MonkeyPatch, secrets_root: Path
) -> None:
    collected: list[list[dict[str, str]]] = []

    class FakeContext:
        def add_cookies(self, cookies: list[dict[str, str]]) -> None:
            collected.append(cookies)

    monkeypatch.setattr(injectors, "load_cookie_files", lambda names: [])

    injectors.inject_cookies(FakeContext(), "demo")

    assert collected == []


# def test_get_form_auth_returns_combined_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
#     monkeypatch.setattr(injectors, "load_form_auth_files", lambda names: {"username": "admin"})
#
#     creds = injectors.get_form_auth("sauce_demo")
#
#     assert creds == {"username": "admin"}
