"""Repository implementations -- the AssessmentRepository port over SQLAlchemy.

Translation between the domain model and the row happens here and nowhere else,
so the pipeline never learns that a database exists.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.domain.errors import ConflictError
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    Assessment,
    Brand,
    KnowledgeDocument,
    RetrievedChunk,
    VisualAnalysis,
)
from backend.app.infra.db.models import (
    AssessmentRow,
    BrandRow,
    KnowledgeDocumentRow,
)
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

    async def list_recent(
        self, *, limit: int = 20, offset: int = 0
    ) -> list[Assessment]:
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


def _brand_to_domain(row: BrandRow, document_count: int = 0) -> Brand:
    return Brand(
        id=row.id,
        name=row.name,
        created_at=row.created_at,
        document_count=document_count,
    )


def _document_to_domain(row: KnowledgeDocumentRow) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=row.id,
        brand_id=row.brand_id,
        filename=row.filename,
        content_sha256=row.content_sha256,
        chunk_count=row.chunk_count,
        created_at=row.created_at,
    )


class SqlBrandRepository:
    """Implements the BrandRepository port."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, name: str) -> Brand:
        async with session_scope(self._session_factory) as session:
            existing = (
                await session.execute(select(BrandRow).where(BrandRow.name == name))
            ).scalar_one_or_none()
            if existing is not None:
                raise ConflictError(f"a brand named {name!r} already exists")
            row = BrandRow(id=str(uuid.uuid4()), name=name)
            session.add(row)
            await session.flush()
            return _brand_to_domain(row)

    async def get(self, brand_id: str) -> Brand | None:
        async with session_scope(self._session_factory) as session:
            row = await session.get(BrandRow, brand_id)
            if row is None:
                return None
            return _brand_to_domain(row, await self._count_documents(session, brand_id))

    async def get_by_name(self, name: str) -> Brand | None:
        async with session_scope(self._session_factory) as session:
            row = (
                await session.execute(select(BrandRow).where(BrandRow.name == name))
            ).scalar_one_or_none()
            if row is None:
                return None
            return _brand_to_domain(row, await self._count_documents(session, row.id))

    async def list_brands(self) -> list[Brand]:
        async with session_scope(self._session_factory) as session:
            rows = (
                await session.execute(select(BrandRow).order_by(BrandRow.name))
            ).scalars().all()
            return [
                _brand_to_domain(row, await self._count_documents(session, row.id))
                for row in rows
            ]

    async def delete(self, brand_id: str) -> bool:
        async with session_scope(self._session_factory) as session:
            row = await session.get(BrandRow, brand_id)
            if row is None:
                return False
            await session.delete(row)
            return True

    async def add_document(
        self,
        brand_id: str,
        filename: str,
        content: str,
        content_sha256: str,
        chunk_count: int,
    ) -> KnowledgeDocument:
        async with session_scope(self._session_factory) as session:
            # Re-uploading the same filename replaces the previous version
            # rather than accumulating near-duplicates in the corpus.
            existing = (
                await session.execute(
                    select(KnowledgeDocumentRow).where(
                        KnowledgeDocumentRow.brand_id == brand_id,
                        KnowledgeDocumentRow.filename == filename,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                await session.delete(existing)
                await session.flush()

            row = KnowledgeDocumentRow(
                id=str(uuid.uuid4()),
                brand_id=brand_id,
                filename=filename,
                content=content,
                content_sha256=content_sha256,
                chunk_count=chunk_count,
            )
            session.add(row)
            await session.flush()
            return _document_to_domain(row)

    async def list_documents(self, brand_id: str) -> list[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocumentRow)
            .where(KnowledgeDocumentRow.brand_id == brand_id)
            .order_by(KnowledgeDocumentRow.filename)
        )
        async with session_scope(self._session_factory) as session:
            rows = (await session.execute(stmt)).scalars().all()
            return [_document_to_domain(row) for row in rows]

    async def find_document_by_hash(
        self, brand_id: str, content_sha256: str
    ) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocumentRow).where(
            KnowledgeDocumentRow.brand_id == brand_id,
            KnowledgeDocumentRow.content_sha256 == content_sha256,
        )
        async with session_scope(self._session_factory) as session:
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _document_to_domain(row) if row else None

    @staticmethod
    async def _count_documents(session: AsyncSession, brand_id: str) -> int:
        stmt = select(func.count()).select_from(KnowledgeDocumentRow).where(
            KnowledgeDocumentRow.brand_id == brand_id
        )
        return int((await session.execute(stmt)).scalar_one())
