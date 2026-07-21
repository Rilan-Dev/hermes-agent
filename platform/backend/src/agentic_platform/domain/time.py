from __future__ import annotations

from datetime import datetime, timezone

from .errors import DomainValidationError


def require_utc(value: datetime, *, field: str = "datetime") -> datetime:
    """Validate a timezone-aware datetime and normalize it to UTC."""

    if not isinstance(value, datetime):
        raise DomainValidationError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
