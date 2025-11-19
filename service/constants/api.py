# service/constants/api.py
"""Canonical header names to prevent typos."""
# Why: APIs and tests should import these, not hardcode strings.
from enum import StrEnum, unique

API_TITLE = "AutoSuite Service"
API_VERSION = "1.0.0"  # semver for API surface (not DB/app version)
API_V1_PREFIX = "/api/v1"  # URL path prefix


class Header(StrEnum):
    API_KEY = "X-API-Key"
    REQUEST_ID = "X-Request-ID"
    CONTENT_TYPE_JSON = "application/json"
    CORRELATION_ID = "X-Correlation-Id"
    IDEMPOTENCY_KEY = "Idempotency-Key"
    RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
    RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET = "X-RateLimit-Reset"


@unique
class Route(StrEnum):
    JOBS = "/jobs"
    CANCEL = "/{id}/cancel"
    HEALTHZ = "/healthz"
    LIVEZ = "/livez"
    METRICS = "/metrics"
