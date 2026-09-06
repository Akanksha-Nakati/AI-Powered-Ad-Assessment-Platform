"""Assessment orchestration: vision -> retrieve -> score.

This module is the reason the ports exist. It contains the pipeline logic and
imports no SDK, so the whole flow is exercised in tests against fakes.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from backend.app.domain.criteria import Criterion
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    Assessment,
    RetrievedChunk,
    VisualAnalysis,
)
from backend.app.domain.ports import KnowledgeStore, Scorer, VisionAnalyzer


def build_retrieval_query(analysis: VisualAnalysis, metadata: AdMetadata) -> str:
    """Turn the creative and its placement into a retrieval query.

    Kept as a free function so it can be tested and tuned without standing up
    the service.
    """
    observed = ", ".join(filter(None, [analysis.cta, analysis.layout, analysis.text]))
    return (
        f"Best practices for {metadata.platform} ads in {metadata.industry} "
        f"for {metadata.ad_type}. Consider call-to-action, color, clarity, attention. "
        f"Creative notes: {observed}"
    )


class AssessmentService:
    def __init__(
        self,
        vision: VisionAnalyzer,
        scorer: Scorer,
        knowledge: KnowledgeStore,
        *,
        retrieval_k: int | None = None,
        prompt_version: str = "v1",
        provider_info: dict[str, str] | None = None,
    ) -> None:
        self._vision = vision
        self._scorer = scorer
        self._knowledge = knowledge
        self._retrieval_k = retrieval_k
        self._prompt_version = prompt_version
        self._provider_info = provider_info or {}

    async def assess(
        self,
        image: bytes,
        media_type: str,
        metadata: AdMetadata,
        *,
        brand_id: str | None = None,
    ) -> Assessment:
        analysis = await self._vision.analyze(image, media_type)

        query = build_retrieval_query(analysis, metadata)
        context = await self._knowledge.retrieve(
            query, k=self._retrieval_k, brand_id=brand_id
        )

        scorecard = await self._scorer.score(analysis, context, metadata)
        scorecard = _with_derived_overall(scorecard)

        return Assessment(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            metadata=metadata,
            scorecard=scorecard,
            visual_analysis=analysis,
            context=context,
            image_sha256=hashlib.sha256(image).hexdigest(),
            provider_info={**self._provider_info, "prompt_version": self._prompt_version},
        )


def _with_derived_overall(scorecard: AdScorecard) -> AdScorecard:
    """Recompute ``overall_score`` from the per-criterion scores.

    Providers are inconsistent about whether their stated overall matches their
    own numbers. Deriving it means the headline figure and the bars in the UI
    can never disagree.
    """
    if not scorecard.scores:
        return scorecard
    mean = sum(scorecard.scores.values()) / len(scorecard.scores)
    return scorecard.model_copy(update={"overall_score": round(mean, 2)})


def missing_criteria(scorecard: AdScorecard) -> list[Criterion]:
    """Criteria the provider failed to score. Used to reject partial results."""
    return [c for c in Criterion if c not in scorecard.scores]
