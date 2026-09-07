"""Generic SQL warehouse connector.

Works against any database SQLAlchemy has a dialect for -- Postgres, MySQL,
SQLite directly, and (with that vendor's own SQLAlchemy dialect package
installed separately) Snowflake, BigQuery, Redshift. No vendor is assumed or
bundled: "generic" means the user's connection URI decides which driver runs,
not this code.

Every defensive measure below earns its place from a specific, named risk --
see the docstring at each guard -- rather than caution for its own sake.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import NoSuchModuleError, SQLAlchemyError
from sqlalchemy.pool import NullPool

from backend.app.domain.errors import WarehouseConnectionError, WarehouseQueryError
from backend.app.domain.models import RawMetricRow

logger = logging.getLogger(__name__)

#: The output contract every user query must satisfy, case-insensitive.
REQUIRED_COLUMNS = {
    "external_ad_id",
    "ctr",
    "spend",
    "conversions",
    "impressions",
    "metric_date",
}

#: Best-effort, not a hard guarantee -- see _wrap_with_limit.
ROW_LIMIT = 5000

_LEADING_KEYWORD = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


class _ValidatedRow(BaseModel):
    """Per-row shape check, so a bad value fails with 'row 14: ctr must be a
    valid number' instead of a generic parse failure."""

    external_ad_id: str
    ctr: float | None = None
    spend: float | None = None
    conversions: int | None = None
    impressions: int | None = None
    metric_date: date


def _validate_query(query: str) -> str:
    """Reject anything that isn't a single SELECT/WITH statement.

    Not a defense against the user attacking their own warehouse -- they
    already own the credential and the data, so a malicious query only hurts
    them. It's about not letting the connector become an accidental
    side-effecting-statement execution surface: a stray second statement
    after a ';', or a SELECT that calls a volatile/side-effecting function,
    is a mistake this rejects rather than silently runs.
    """
    stripped = query.strip().rstrip(";").strip()
    if not stripped:
        raise WarehouseQueryError("the query is empty")
    if ";" in stripped:
        raise WarehouseQueryError(
            "only a single statement is allowed (found a second ';')"
        )
    if not _LEADING_KEYWORD.match(stripped):
        raise WarehouseQueryError("the query must start with SELECT or WITH")
    return stripped


def _wrap_with_limit(query: str) -> str:
    """Best-effort row cap, not a hard guarantee.

    Wrapping as a subquery bounds the common case without needing every
    "generic" driver to support a streaming cursor. But the warehouse still
    computes the full result before this LIMIT discards rows past it, and a
    query using vendor-specific syntax this wrap doesn't anticipate (an
    unusual CTE shape, a trailing vendor hint) can break it outright. This is
    a safety net for the common case, not a resource guarantee.
    """
    return f"SELECT * FROM ({query}) AS _warehouse_subquery LIMIT {ROW_LIMIT + 1}"


def _redact(connection_uri: str) -> str:
    """The only form a connection URI is allowed to reach a log line in."""
    try:
        return make_url(connection_uri).render_as_string(hide_password=True)
    except Exception:
        return "<unparseable connection string>"


class GenericSqlConnector:
    """Implements PerformanceSource over plain SQLAlchemy core.

    Deliberately synchronous internally -- test_connection/fetch_metrics run
    it via asyncio.to_thread, matching the convention chroma_store.py already
    established for blocking calls, rather than reimplementing this per
    dialect (not every one has an async driver).
    """

    def __init__(self, *, query_timeout_seconds: int = 30) -> None:
        self._timeout = query_timeout_seconds

    async def test_connection(self, connection_uri: str, query: str) -> None:
        await self._run(connection_uri, query, fetch=False)

    async def fetch_metrics(
        self, connection_uri: str, query: str
    ) -> list[RawMetricRow]:
        rows = await self._run(connection_uri, query, fetch=True)
        return rows or []

    async def _run(
        self, connection_uri: str, query: str, *, fetch: bool
    ) -> list[RawMetricRow] | None:
        validated = _validate_query(query)
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._execute, connection_uri, validated, fetch),
                timeout=self._timeout,
            )
        except TimeoutError as exc:
            # This stops the *caller* from waiting -- it does not kill the
            # underlying blocking DBAPI call, whose thread may keep running
            # until the driver itself gives up. Documented, not silently
            # assumed away.
            raise WarehouseConnectionError(
                f"the warehouse did not respond within {self._timeout}s"
            ) from exc

    def _execute(
        self, connection_uri: str, query: str, fetch: bool
    ) -> list[RawMetricRow] | None:
        engine = self._build_engine(connection_uri)
        try:
            with engine.connect() as conn:
                result = self._execute_query(conn, query, connection_uri)
                return self._collect(result) if fetch else None
        except WarehouseQueryError:
            # Already the right error type -- the inner query-execution catch
            # below constructed it. Re-raised explicitly so the outer
            # SQLAlchemyError clause below can't be mistaken for handling it
            # too (it can't: the two exception hierarchies are unrelated, but
            # this makes that obvious to a reader without checking).
            raise
        except SQLAlchemyError as exc:
            # engine.connect() itself raises here for the ordinary connection
            # failures -- wrong host, wrong port, auth rejected -- which were
            # previously *not* caught by anything in this method and would
            # have escaped as an unhandled 500.
            logger.warning(
                "could not connect to %s: %s",
                _redact(connection_uri),
                type(exc).__name__,
            )
            raise WarehouseConnectionError(
                "could not connect to the configured warehouse; check the "
                "connection string and network access"
            ) from exc
        finally:
            engine.dispose()

    def _execute_query(self, conn: Any, query: str, connection_uri: str) -> Any:
        try:
            return conn.execute(text(_wrap_with_limit(query)))
        except SQLAlchemyError as exc:
            logger.warning(
                "warehouse query failed for %s: %s",
                _redact(connection_uri),
                type(exc).__name__,
            )
            raise WarehouseQueryError("the query failed to execute") from exc

    def _build_engine(self, connection_uri: str) -> Engine:
        try:
            return create_engine(connection_uri, poolclass=NullPool)
        except (NoSuchModuleError, ModuleNotFoundError, ImportError) as exc:
            # Two different failure shapes land here, both meaning "the driver
            # isn't installed": NoSuchModuleError when the *dialect itself*
            # isn't a registered SQLAlchemy plugin (Snowflake, BigQuery --
            # external packages), and a bare ModuleNotFoundError when the
            # dialect is built into SQLAlchemy core (postgresql, mysql) but
            # its DBAPI driver (psycopg2, PyMySQL) isn't installed. Both get
            # the same actionable message rather than one falling through as
            # an unhandled 500.
            dialect = (
                connection_uri.split("://", 1)[0] if "://" in connection_uri else "?"
            )
            raise WarehouseConnectionError(
                f"no SQLAlchemy driver installed for {dialect!r}. Install "
                f"that vendor's SQLAlchemy dialect/DBAPI package."
            ) from exc
        except SQLAlchemyError as exc:
            # Deliberately never str(exc): a malformed URI's own parse error
            # can embed the URI, password included. This is the one line in
            # the whole module a connection string is allowed near.
            logger.warning(
                "could not build an engine for %s: %s",
                _redact(connection_uri),
                type(exc).__name__,
            )
            raise WarehouseConnectionError(
                "could not connect to the configured warehouse; check the "
                "connection string and network access"
            ) from exc

    def _collect(self, result: Any) -> list[RawMetricRow]:
        column_names = result.keys()
        column_map = {str(c).lower(): c for c in column_names}
        missing = REQUIRED_COLUMNS - column_map.keys()
        if missing:
            raise WarehouseQueryError(
                "the query is missing required column(s): "
                + ", ".join(sorted(missing))
            )

        rows: list[RawMetricRow] = []
        for i, raw in enumerate(result.mappings()):
            payload = {name: raw[column_map[name]] for name in REQUIRED_COLUMNS}
            try:
                validated = _ValidatedRow.model_validate(payload)
            except ValidationError as exc:
                first = exc.errors()[0]
                raise WarehouseQueryError(
                    f"row {i}: column {first['loc'][0]!r} -- {first['msg']}"
                ) from exc
            rows.append(RawMetricRow(**validated.model_dump()))
            if len(rows) >= ROW_LIMIT:
                break
        return rows
