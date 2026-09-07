"""GenericSqlConnector against a real (if disposable) SQLite database.

FakePerformanceSource in fakes.py is trivial to get right, which proves
nothing about the real adapter it stands in for -- that's exactly the gap
that let brand-scoped retrieval silently not work earlier in this project,
because only the fake knowledge store was ever exercised. This file is the
counterpart for the warehouse connector: connect, query, reject bad shape,
reject non-SELECT, cap rows, and never leak a credential in an error.
"""

from __future__ import annotations

import sqlite3

import pytest

from backend.app.domain.errors import WarehouseConnectionError, WarehouseQueryError
from backend.app.infra.warehouse.sql_connector import ROW_LIMIT, GenericSqlConnector


@pytest.fixture
def warehouse_uri(tmp_path):
    """A throwaway SQLite file standing in as 'a data warehouse', seeded with
    a table that does not itself use the app's own column names -- the
    connector's job is to translate the user's SELECT into the fixed
    contract, not to assume the warehouse's schema matches it."""
    db_path = tmp_path / "warehouse.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE ad_performance (
            ad_ref TEXT, click_rate REAL, spend_usd REAL,
            conv_count INTEGER, impr_count INTEGER, day TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO ad_performance VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("campaign-1", 0.021, 120.50, 4, 5000, "2026-01-01"),
            ("campaign-2", 0.045, 80.00, 9, 3000, "2026-01-01"),
        ],
    )
    conn.commit()
    conn.close()
    return f"sqlite:///{db_path}"


CONTRACT_QUERY = (
    "SELECT ad_ref AS external_ad_id, click_rate AS ctr, spend_usd AS spend, "
    "conv_count AS conversions, impr_count AS impressions, day AS metric_date "
    "FROM ad_performance"
)


async def test_fetch_metrics_against_a_real_warehouse(warehouse_uri):
    connector = GenericSqlConnector()

    rows = await connector.fetch_metrics(warehouse_uri, CONTRACT_QUERY)

    assert {r.external_ad_id for r in rows} == {"campaign-1", "campaign-2"}
    by_id = {r.external_ad_id: r for r in rows}
    assert by_id["campaign-1"].ctr == pytest.approx(0.021)
    assert by_id["campaign-1"].conversions == 4
    assert str(by_id["campaign-1"].metric_date) == "2026-01-01"


async def test_test_connection_succeeds_against_a_real_warehouse(warehouse_uri):
    # Must not raise.
    await GenericSqlConnector().test_connection(warehouse_uri, CONTRACT_QUERY)


async def test_test_connection_against_an_unreachable_database(tmp_path):
    connector = GenericSqlConnector()
    bad_uri = f"sqlite:///{tmp_path / 'does_not_exist' / 'nope.db'}"

    with pytest.raises(WarehouseConnectionError):
        await connector.test_connection(bad_uri, CONTRACT_QUERY)


async def test_missing_required_column_is_rejected(warehouse_uri):
    connector = GenericSqlConnector()
    incomplete = "SELECT ad_ref AS external_ad_id, click_rate AS ctr FROM ad_performance"

    with pytest.raises(WarehouseQueryError, match="spend"):
        await connector.fetch_metrics(warehouse_uri, incomplete)


async def test_non_select_query_is_rejected(warehouse_uri):
    connector = GenericSqlConnector()

    with pytest.raises(WarehouseQueryError, match="SELECT or WITH"):
        await connector.fetch_metrics(warehouse_uri, "DELETE FROM ad_performance")


async def test_multi_statement_query_is_rejected(warehouse_uri):
    connector = GenericSqlConnector()
    injected = CONTRACT_QUERY + "; DROP TABLE ad_performance;"

    with pytest.raises(WarehouseQueryError, match="single statement"):
        await connector.fetch_metrics(warehouse_uri, injected)


async def test_a_with_query_is_accepted(warehouse_uri):
    """WITH is a legitimate way to start a read query (a CTE), not just
    SELECT -- the validator must not reject it."""
    connector = GenericSqlConnector()
    cte_query = f"WITH ranked AS ({CONTRACT_QUERY}) SELECT * FROM ranked"

    rows = await connector.fetch_metrics(warehouse_uri, cte_query)
    assert len(rows) == 2


async def test_row_cap_is_enforced(tmp_path):
    """The wrap is a best-effort safety net, not a resource guarantee -- but
    it must still actually cap what fetch_metrics returns to the caller."""
    db_path = tmp_path / "big_warehouse.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE ads (ad_ref TEXT, ctr REAL, spend REAL, "
        "conversions INTEGER, impressions INTEGER, metric_date TEXT)"
    )
    conn.executemany(
        "INSERT INTO ads VALUES (?, 0.01, 1.0, 1, 100, '2026-01-01')",
        [(f"ad-{i}",) for i in range(ROW_LIMIT + 10)],
    )
    conn.commit()
    conn.close()

    connector = GenericSqlConnector()
    rows = await connector.fetch_metrics(
        f"sqlite:///{db_path}",
        "SELECT ad_ref AS external_ad_id, ctr, spend, conversions, "
        "impressions, metric_date FROM ads",
    )

    assert len(rows) == ROW_LIMIT


async def test_credential_never_leaks_into_the_error_message():
    """The one test that would have caught a real credential leak: a
    connection string with an embedded password must never appear -- in any
    form -- in what the connector raises."""
    connector = GenericSqlConnector()
    secret_uri = "postgresql://warehouse_user:s3cr3t-password@127.0.0.1:1/nope"

    with pytest.raises((WarehouseConnectionError, WarehouseQueryError)) as excinfo:
        await connector.test_connection(secret_uri, CONTRACT_QUERY)

    assert "s3cr3t-password" not in str(excinfo.value)
