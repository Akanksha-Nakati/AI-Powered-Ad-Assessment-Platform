"""SQLAlchemy tables.

Deliberately separate from the domain models in app/domain/models.py. The
domain model is what the application reasons about and what the API returns;
this is how it happens to be stored. Keeping them apart is what lets the
storage schema change (or move to Postgres) without touching the pipeline.

JSON columns are used for the scorecard, visual analysis and retrieved context:
they are read and written whole, never queried field-by-field, so normalising
them would add joins that buy nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.app.infra.db.types import UtcDateTime


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AssessmentRow(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, nullable=False
    )

    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    industry: Mapped[str] = mapped_column(String(64), nullable=False)
    ad_type: Mapped[str] = mapped_column(String(64), nullable=False)

    image_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    overall_score: Mapped[float] = mapped_column(nullable=False)

    scorecard: Mapped[dict] = mapped_column(JSON, nullable=False)
    visual_analysis: Mapped[dict] = mapped_column(JSON, nullable=False)
    context: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    provider_info: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    #: sha256 of (image, placement, prompt version, model). Unique so an
    #: identical re-submission is served from here instead of re-billing two
    #: model calls.
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    __table_args__ = (
        Index("ix_assessments_created_at_desc", created_at.desc()),
    )


class BrandRow(Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, nullable=False
    )

    documents: Mapped[list[KnowledgeDocumentRow]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )


class KnowledgeDocumentRow(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brand_id: Mapped[str] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    #: Lets ingestion skip re-embedding an unchanged document.
    content_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, nullable=False
    )

    brand: Mapped[BrandRow] = relationship(back_populates="documents")


class ComparisonRow(Base):
    __tablename__ = "comparisons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, nullable=False
    )
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    industry: Mapped[str] = mapped_column(String(64), nullable=False)
    ad_type: Mapped[str] = mapped_column(String(64), nullable=False)
    #: Assessment ids in ranked order, best first.
    ranked_assessment_ids: Mapped[list] = mapped_column(JSON, nullable=False)
