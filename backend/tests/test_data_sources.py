"""Data-warehouse connections and score-vs-performance correlation."""

from __future__ import annotations

import pytest

from backend.app.domain.errors import ConflictError, NotFoundError
from backend.app.domain.models import AdMetadata, RawMetricRow
from backend.app.services.performance_service import PerformanceService, _pearson
from backend.tests.fakes import (
    FakeAssessmentRepository,
    FakeDataSourceRepository,
    FakePerformanceSource,
    _full_scorecard,
)

CREATE_PAYLOAD = {
    "name": "Snowflake prod",
    "dialect": "Snowflake",
    "connection_uri": "snowflake://user:s3cr3t-password@acct/db",
    "query": "SELECT external_ad_id, ctr, spend, conversions, impressions, "
    "metric_date FROM ad_metrics",
}


# --- API ---------------------------------------------------------------


def test_create_and_list_data_sources(make_client):
    client, _ = make_client()

    created = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD)
    assert created.status_code == 201
    assert created.json()["name"] == "Snowflake prod"
    assert created.json()["dialect"] == "Snowflake"

    listed = client.get("/api/v1/data-sources").json()
    assert [c["name"] for c in listed] == ["Snowflake prod"]


def test_the_connection_secret_never_appears_in_any_response(make_client):
    """connection_uri and query are write-only. This is the regression test
    for that guarantee, not just a hope resting on the response model."""
    client, _ = make_client()
    created = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD)

    connection_id = created.json()["id"]
    for response in (
        created,
        client.get("/api/v1/data-sources"),
        client.get(f"/api/v1/data-sources/{connection_id}"),
    ):
        body = response.text
        assert "s3cr3t-password" not in body
        assert "connection_uri" not in body
        assert "query" not in body


def test_duplicate_data_source_name_is_409(make_client):
    client, _ = make_client()
    client.post("/api/v1/data-sources", json=CREATE_PAYLOAD)

    conflict = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD)
    assert conflict.status_code == 409


def test_unknown_data_source_is_404(make_client):
    client, _ = make_client()
    assert client.get("/api/v1/data-sources/no-such-id").status_code == 404


def test_delete_data_source(make_client):
    client, _ = make_client()
    connection_id = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD).json()["id"]

    assert client.delete(f"/api/v1/data-sources/{connection_id}").status_code == 204
    assert client.get(f"/api/v1/data-sources/{connection_id}").status_code == 404


def test_test_connection_records_success(make_client):
    client, _ = make_client(warehouse=FakePerformanceSource())
    connection_id = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD).json()["id"]

    tested = client.post(f"/api/v1/data-sources/{connection_id}/test")

    assert tested.status_code == 200
    assert tested.json()["last_test_ok"] is True
    assert tested.json()["last_tested_at"] is not None


def test_test_connection_records_failure_and_surfaces_as_502(make_client):
    from backend.app.domain.errors import WarehouseConnectionError

    warehouse = FakePerformanceSource(error=WarehouseConnectionError("unreachable"))
    client, _ = make_client(warehouse=warehouse)
    connection_id = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD).json()["id"]

    tested = client.post(f"/api/v1/data-sources/{connection_id}/test")
    assert tested.status_code == 502

    # The failure is still recorded, not silently dropped.
    stored = client.get(f"/api/v1/data-sources/{connection_id}").json()
    assert stored["last_test_ok"] is False


def test_refresh_pulls_and_stores_metrics(make_client):
    rows = [
        RawMetricRow(
            external_ad_id="ad-1", ctr=0.02, spend=100.0, conversions=3,
            impressions=1000, metric_date="2026-01-01",
        )
    ]
    client, _ = make_client(warehouse=FakePerformanceSource(rows=rows))
    connection_id = client.post("/api/v1/data-sources", json=CREATE_PAYLOAD).json()["id"]

    refreshed = client.post(f"/api/v1/data-sources/{connection_id}/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["rows_fetched"] == 1


# --- the actual point: does the join (and the correlation) really work ----


def _tagged_assessment(external_ad_id: str, overall_score: float):
    from datetime import UTC, datetime

    from backend.app.domain.models import Assessment
    from backend.tests.fakes import SAMPLE_ANALYSIS, SAMPLE_CHUNKS

    return Assessment(
        id=f"assessment-{external_ad_id}",
        created_at=datetime.now(UTC),
        metadata=AdMetadata(platform="TikTok", industry="SaaS", ad_type="Banner"),
        scorecard=_full_scorecard(overall_score=overall_score),
        visual_analysis=SAMPLE_ANALYSIS,
        context=SAMPLE_CHUNKS,
        provider_info={"cache_key": f"key-{external_ad_id}"},
        external_ad_id=external_ad_id,
    )


async def test_correlation_matches_tagged_assessments_to_warehouse_rows():
    """The join this whole feature exists for: an assessment's own score,
    lined up against real performance pulled from an external warehouse --
    exercised through the real service, not a hand-computed fixture."""
    assessments = FakeAssessmentRepository()
    for ad_id, score in [("ad-1", 2.0), ("ad-2", 5.0), ("ad-3", 8.0)]:
        assessments.saved.append(_tagged_assessment(ad_id, score))
    # Tagged, but this connection's warehouse pull won't mention it.
    assessments.saved.append(_tagged_assessment("ad-5", 9.0))

    data_sources = FakeDataSourceRepository()
    connection = await data_sources.create("Snowflake prod", "Snowflake", "uri", "q")

    warehouse = FakePerformanceSource(
        rows=[
            RawMetricRow(
                external_ad_id="ad-1", ctr=0.01, spend=10.0, conversions=1,
                impressions=100, metric_date="2026-01-01",
            ),
            RawMetricRow(
                external_ad_id="ad-2", ctr=0.03, spend=20.0, conversions=2,
                impressions=200, metric_date="2026-01-01",
            ),
            RawMetricRow(
                external_ad_id="ad-3", ctr=0.05, spend=30.0, conversions=3,
                impressions=300, metric_date="2026-01-01",
            ),
            # No assessment is tagged with this id.
            RawMetricRow(
                external_ad_id="ad-4", ctr=0.02, spend=15.0, conversions=1,
                impressions=150, metric_date="2026-01-01",
            ),
        ]
    )
    service = PerformanceService(data_sources, warehouse, assessments)
    await service.refresh_metrics(connection.id)

    result = await service.get_correlation(connection.id)

    assert result.matched_count == 3
    assert {p.external_ad_id for p in result.points} == {"ad-1", "ad-2", "ad-3"}
    assert result.unmatched_metrics == 1, "ad-4 has no tagged assessment"
    assert result.unmatched_assessments == 1, "ad-5 is tagged but absent from this pull"
    # x=[2,5,8], y=[.01,.03,.05] is a perfect line -- r must be 1.0.
    assert result.pearson_r == pytest.approx(1.0)


async def test_correlation_on_an_unknown_connection_is_404():
    assessments = FakeAssessmentRepository()
    data_sources = FakeDataSourceRepository()
    service = PerformanceService(data_sources, FakePerformanceSource(), assessments)

    with pytest.raises(NotFoundError):
        await service.get_correlation("no-such-id")


# --- service-level --------------------------------------------------------


async def test_service_rejects_blank_data_source_name():
    service = PerformanceService(
        FakeDataSourceRepository(), FakePerformanceSource(), FakeAssessmentRepository()
    )
    with pytest.raises(ConflictError):
        await service.create_connection("   ", "Postgres", "uri", "query")


async def test_service_raises_not_found_for_unknown_connection():
    service = PerformanceService(
        FakeDataSourceRepository(), FakePerformanceSource(), FakeAssessmentRepository()
    )
    with pytest.raises(NotFoundError):
        await service.delete_connection("no-such-id")


# --- Pearson's r, as a free function (same reasoning as build_cache_key) ---


def test_pearson_perfect_positive_correlation():
    assert _pearson([(1, 1), (2, 2), (3, 3)]) == pytest.approx(1.0)


def test_pearson_perfect_negative_correlation():
    assert _pearson([(1, 3), (2, 2), (3, 1)]) == pytest.approx(-1.0)


def test_pearson_is_none_below_two_points():
    assert _pearson([]) is None
    assert _pearson([(1, 1)]) is None


def test_pearson_is_none_when_an_axis_has_zero_variance():
    assert _pearson([(1, 5), (1, 8), (1, 2)]) is None, "x never varies"
    assert _pearson([(1, 5), (2, 5), (3, 5)]) is None, "y never varies"
