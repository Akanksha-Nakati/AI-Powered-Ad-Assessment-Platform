"""Data-warehouse connections, metric pulls, and score-vs-performance correlation.

This is what turns "did our creative score actually predict anything real"
from a slogan into a number: connect a warehouse, tag assessments with the
same identifier the warehouse uses for that ad, and get_correlation computes
Pearson's r between overall_score and CTR over whatever intersection exists.
"""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.domain.errors import ConflictError, NotFoundError
from backend.app.domain.models import (
    CorrelationPoint,
    CorrelationResult,
    DataSourceConnection,
)
from backend.app.domain.ports import (
    AssessmentRepository,
    DataSourceRepository,
    PerformanceSource,
)


class PerformanceService:
    def __init__(
        self,
        connections: DataSourceRepository,
        source: PerformanceSource,
        assessments: AssessmentRepository,
    ) -> None:
        self._connections = connections
        self._source = source
        self._assessments = assessments

    async def create_connection(
        self, name: str, dialect: str, connection_uri: str, query: str
    ) -> DataSourceConnection:
        name = name.strip()
        if not name:
            raise ConflictError("data source name cannot be empty")
        return await self._connections.create(name, dialect, connection_uri, query)

    async def list_connections(self) -> list[DataSourceConnection]:
        return await self._connections.list_connections()

    async def get_connection(self, connection_id: str) -> DataSourceConnection:
        connection = await self._connections.get(connection_id)
        if connection is None:
            raise NotFoundError(f"no data source with id {connection_id}")
        return connection

    async def delete_connection(self, connection_id: str) -> None:
        if not await self._connections.delete(connection_id):
            raise NotFoundError(f"no data source with id {connection_id}")

    async def test_connection(self, connection_id: str) -> DataSourceConnection:
        uri, query = await self._require_secret(connection_id)
        now = datetime.now(UTC)
        try:
            await self._source.test_connection(uri, query)
        except Exception:
            await self._connections.record_test_result(connection_id, False, now)
            raise
        await self._connections.record_test_result(connection_id, True, now)
        return await self.get_connection(connection_id)

    async def refresh_metrics(self, connection_id: str) -> int:
        uri, query = await self._require_secret(connection_id)
        rows = await self._source.fetch_metrics(uri, query)
        count = await self._connections.save_metrics(connection_id, rows)
        await self._connections.record_test_result(
            connection_id, True, datetime.now(UTC)
        )
        return count

    async def get_correlation(self, connection_id: str) -> CorrelationResult:
        await self.get_connection(connection_id)  # 404s early if unknown

        aggregated: dict[str, _Aggregate] = {}
        for metric in await self._connections.list_metrics(connection_id):
            aggregated.setdefault(metric.external_ad_id, _Aggregate()).add(
                metric.ctr, metric.spend, metric.conversions
            )

        matching_assessments = {
            a.external_ad_id: a
            for a in await self._assessments.list_by_external_ids(list(aggregated))
            if a.external_ad_id
        }

        points: list[CorrelationPoint] = []
        for external_ad_id, agg in aggregated.items():
            assessment = matching_assessments.get(external_ad_id)
            if assessment is None:
                continue
            points.append(
                CorrelationPoint(
                    assessment_id=assessment.id,
                    external_ad_id=external_ad_id,
                    overall_score=assessment.scorecard.overall_score,
                    avg_ctr=agg.avg_ctr,
                    total_spend=agg.total_spend,
                    total_conversions=agg.total_conversions,
                    sample_size=agg.count,
                )
            )

        matched_ids = {p.external_ad_id for p in points}
        all_tagged_ids = {
            a.external_ad_id
            for a in await self._assessments.list_tagged()
            if a.external_ad_id
        }

        return CorrelationResult(
            points=points,
            pearson_r=_pearson(
                [(p.overall_score, p.avg_ctr) for p in points if p.avg_ctr is not None]
            ),
            matched_count=len(points),
            unmatched_assessments=len(all_tagged_ids - matched_ids),
            unmatched_metrics=len(aggregated) - len(points),
        )

    async def _require_secret(self, connection_id: str) -> tuple[str, str]:
        secret = await self._connections.get_connection_secret(connection_id)
        if secret is None:
            raise NotFoundError(f"no data source with id {connection_id}")
        return secret


class _Aggregate:
    """Per-external_ad_id rollup across however many metric rows share it."""

    def __init__(self) -> None:
        self.count = 0
        self._ctr_sum = 0.0
        self._ctr_count = 0
        self.total_spend: float | None = None
        self.total_conversions: int | None = None

    def add(
        self, ctr: float | None, spend: float | None, conversions: int | None
    ) -> None:
        self.count += 1
        if ctr is not None:
            self._ctr_sum += ctr
            self._ctr_count += 1
        if spend is not None:
            self.total_spend = (self.total_spend or 0.0) + spend
        if conversions is not None:
            self.total_conversions = (self.total_conversions or 0) + conversions

    @property
    def avg_ctr(self) -> float | None:
        return self._ctr_sum / self._ctr_count if self._ctr_count else None


def _pearson(pairs: list[tuple[float, float]]) -> float | None:
    """None below 2 points or when either axis has zero variance -- the
    coefficient is undefined there, not just noisy. A free function so it can
    be tested without standing up the service, same reasoning as
    assessment_service.build_cache_key."""
    n = len(pairs)
    if n < 2:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    variance_x = sum((x - mean_x) ** 2 for x in xs)
    variance_y = sum((y - mean_y) ** 2 for y in ys)
    if variance_x == 0 or variance_y == 0:
        return None
    return covariance / (variance_x * variance_y) ** 0.5
