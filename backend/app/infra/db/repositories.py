"""Repository implementations -- the AssessmentRepository port over SQLAlchemy.

Translation between the domain model and the row happens here and nowhere else,
so the pipeline never learns that a database exists.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    Assessment,
    RetrievedChunk,
    VisualAnalysis,
)
from backend.app.infra.db.models import AssessmentRow
from backend.app.infra.db.session import session_scope


def _to_domain(row: AssessmentRow) -> Assessment:
    return Assessment(
        id=row.id,
        created_at=row.created_at,
        metadata=AdMetadata(
            platform=row.platform, industry=row.industry, ad_type=row.ad_type
        ),
        scorecard=AdScorecard.model_validate(row.scorecard),
        visual_analysis=VisualAnalysis.model_validate(row.visual_analysis),
        context=[RetrievedChunk.model_validate(c) for c in row.context],
        image_sha256=row.image_sha256,
        provider_info=row.provider_info,
    )


def _to_row(assessment: Assessment, cache_key: str) -> AssessmentRow:
    return AssessmentRow(
        id=assessment.id,
        created_at=assessment.created_at,
        platform=assessment.metadata.platform,
        industry=assessment.metadata.industry,
        ad_type=assessment.metadata.ad_type,
        image_sha256=assessment.image_sha256,
        overall_score=assessment.scorecard.overall_score,
        scorecard=assessment.scorecard.model_dump(mode="json"),
        visual_analysis=assessment.visual_analysis.model_dump(mode="json"),
        context=[c.model_dump(mode="json") for c in assessment.context],
        provider_info=assessment.provider_info,
        cache_key=cache_key,
    )


class SqlAssessmentRepository:
    """Implements the AssessmentRepository port."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, assessment: Assessment) -> None:
        cache_key = assessment.provider_info.get("cache_key", assessment.id)
        async with session_scope(self._session_factory) as session:
            session.add(_to_row(assessment, cache_key))

    async def get(self, assessment_id: str) -> Assessment | None:
        async with session_scope(self._session_factory) as session:
            row = await session.get(AssessmentRow, assessment_id)
            return _to_domain(row) if row else None

    async def list(self, *, limit: int = 20, offset: int = 0) -> list[Assessment]:
        stmt = (
            select(AssessmentRow)
            .order_by(AssessmentRow.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        async with session_scope(self._session_factory) as session:
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(row) for row in rows]

    async def find_cached(self, cache_key: str) -> Assessment | None:
        stmt = select(AssessmentRow).where(AssessmentRow.cache_key == cache_key)
        async with session_scope(self._session_factory) as session:
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _to_domain(row) if row else None
