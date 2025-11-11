thonfrom __future__ import annotations

import datetime as _dt
from typing import Optional

def now_utc() -> _dt.datetime:
    """Return current UTC time with timezone info."""
    return _dt.datetime.now(tz=_dt.timezone.utc)

def to_iso(dt: _dt.datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.isoformat()

def parse_iso(value: str) -> Optional[_dt.datetime]:
    """Parse an ISO 8601 datetime string safely."""
    try:
        return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

def timestamp_for_filename(dt: Optional[_dt.datetime] = None) -> str:
    """
    Generate a filesystem-friendly timestamp for filenames.

    Example: 2025-11-11T15-43-22Z
    """
    if dt is None:
        dt = now_utc()
    dt = dt.astimezone(_dt.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H-%M-%SZ")