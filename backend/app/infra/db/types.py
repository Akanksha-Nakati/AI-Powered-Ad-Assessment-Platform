"""Custom column types."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator):
    """A timezone-aware datetime that survives SQLite.

    SQLite has no native timestamp type, so ``DateTime(timezone=True)`` accepts
    an aware datetime and hands back a naive one -- the offset is silently
    dropped. That turns a round-trip into a lossy operation and puts naive
    timestamps in the API response, which any client doing date arithmetic
    against a UTC value would get wrong.

    This normalises to UTC on the way in and re-attaches UTC on the way out, so
    the behaviour is identical on SQLite and Postgres.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime passed to a UtcDateTime column")
        return value.astimezone(UTC)

    def process_result_value(
        self, value: Any, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
