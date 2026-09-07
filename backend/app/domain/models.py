"""Core domain models.

These are Pydantic models rather than plain dataclasses on purpose: the same
class is used three ways -- as the provider's enforced output schema, as the
FastAPI response model (and therefore the OpenAPI schema the frontend types are
generated from), and as the in-process domain object. One definition, so the
three cannot drift.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.criteria import Criterion


class AdMetadata(BaseModel):
    """What the user tells us about where the ad will run."""

    model_config = ConfigDict(extra="forbid")

    platform: str
    industry: str
    ad_type: str


class VisualAnalysis(BaseModel):
    """Structured description of the creative, produced by the vision model."""

    model_config = ConfigDict(extra="forbid")

    colors: list[str] = Field(
        default_factory=list, description="Dominant colors, hex where legible."
    )
    text: str = Field("", description="Key copy detected in the creative.")
    layout: str = Field("", description="Composition and focal areas.")
    cta: str = Field("", description="Visible call-to-action text, empty if none.")
    insights: list[str] = Field(
        default_factory=list, description="Short strength/risk observations."
    )


class RetrievedChunk(BaseModel):
    """One passage of marketing guidance pulled from the knowledge store."""

    model_config = ConfigDict(extra="forbid")

    text: str
    source: str
    chunk: int | None = None
    brand_id: str | None = None


class AdScorecard(BaseModel):
    """
    The scoring contract.

    Doubles as the provider output schema, so a provider physically cannot
    return a shape this application does not understand.
    """

    model_config = ConfigDict(extra="forbid")

    scores: dict[Criterion, float] = Field(
        description="One 0-10 score per criterion. All six are required."
    )
    overall_score: float = Field(ge=0, le=10)
    feedback: str = Field(description="A short paragraph of overall assessment.")
    recommendations: list[str] = Field(
        default_factory=list, description="At most five concrete, actionable changes."
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Filenames of the guidance passages the judgement rests on.",
    )


class Assessment(BaseModel):
    """A complete assessment: what was asked, what was seen, what was judged."""

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: datetime
    metadata: AdMetadata
    scorecard: AdScorecard
    visual_analysis: VisualAnalysis
    context: list[RetrievedChunk] = Field(default_factory=list)
    image_sha256: str | None = None
    provider_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Which models and prompt version produced this, for cache keying.",
    )
    external_ad_id: str | None = Field(
        default=None,
        description=(
            "This assessment's identifier in the user's own data warehouse, so "
            "performance metrics pulled from there can be joined back to it. Set "
            "after the fact via PATCH, deliberately not part of build_cache_key: "
            "tagging an assessment must never invalidate its cached scorecard."
        ),
    )


class Brand(BaseModel):
    """An advertiser whose own guidelines augment the global best practices."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    created_at: datetime
    document_count: int = 0


class KnowledgeDocument(BaseModel):
    """One ingested brand document."""

    model_config = ConfigDict(extra="forbid")

    id: str
    brand_id: str
    filename: str
    content_sha256: str
    chunk_count: int
    created_at: datetime


class ComparisonEntry(BaseModel):
    """One variant's placement in a comparison."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1, description="1 is best.")
    label: str = Field(description="The uploaded filename, for identification.")
    assessment: Assessment


class Comparison(BaseModel):
    """Several variants of the same ad, judged together and ranked."""

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: datetime
    metadata: AdMetadata
    entries: list[ComparisonEntry]

    @property
    def winner(self) -> ComparisonEntry | None:
        return self.entries[0] if self.entries else None
