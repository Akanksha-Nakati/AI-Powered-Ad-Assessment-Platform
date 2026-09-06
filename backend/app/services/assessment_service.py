"""Assessment orchestration: cache -> vision -> retrieve -> score -> persist.

This module is the reason the ports exist. It contains the pipeline logic and
imports no SDK, no HTTP client and no database driver, so the whole flow is
exercised in tests against fakes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime

from backend.app.domain.criteria import Criterion
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    Assessment,
    VisualAnalysis,
)
from backend.app.domain.ports import (
    AssessmentRepository,
    BlobStore,
    KnowledgeStore,
    Scorer,
    VisionAnalyzer,
)

logger = logging.getLogger(__name__)


def build_retrieval_query(analysis: VisualAnalysis, metadata: AdMetadata) -> str:
    """Turn the creative and its placement into a retrieval query.

    A free function so it can be tested and tuned without standing up the
    service.
    """
    observed = ", ".join(filter(None, [analysis.cta, analysis.layout, analysis.text]))
    return (
        f"Best practices for {metadata.platform} ads in {metadata.industry} "
        f"for {metadata.ad_type}. Consider call-to-action, color, clarity, attention. "
        f"Creative notes: {observed}"
    )


def build_cache_key(
    image_sha256: str,
    metadata: AdMetadata,
    provider_info: dict[str, str],
    brand_id: str | None,
) -> str:
    """Everything that, if changed, should produce a different verdict.

    The model and prompt version are included deliberately: a prompt edit or a
    model swap must not serve a cached score produced by the previous one.
    """
    payload = {
        "image": image_sha256,
        "metadata": metadata.model_dump(),
        "brand_id": brand_id,
        "providers": dict(sorted(provider_info.items())),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class AssessmentService:
    def __init__(
        self,
        vision: VisionAnalyzer,
        scorer: Scorer,
        knowledge: KnowledgeStore,
        *,
        repository: AssessmentRepository | None = None,
        blobs: BlobStore | None = None,
        retrieval_k: int | None = None,
        prompt_version: str = "v1",
        provider_info: dict[str, str] | None = None,
    ) -> None:
        self._vision = vision
        self._scorer = scorer
        self._knowledge = knowledge
        self._repository = repository
        self._blobs = blobs
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
        use_cache: bool = True,
    ) -> Assessment:
        image_sha256 = hashlib.sha256(image).hexdigest()
        provider_info = {**self._provider_info, "prompt_version": self._prompt_version}
        cache_key = build_cache_key(image_sha256, metadata, provider_info, brand_id)

        if use_cache and self._repository is not None:
            cached = await self._repository.find_cached(cache_key)
            if cached is not None:
                logger.info("assessment cache hit for %s", image_sha256[:12])
                return cached

        if self._blobs is not None:
            await self._blobs.put(image, media_type)

        analysis = await self._vision.analyze(image, media_type)

        query = build_retrieval_query(analysis, metadata)
        context = await self._knowledge.retrieve(
            query, k=self._retrieval_k, brand_id=brand_id
        )

        raw = await self._scorer.score(analysis, context, metadata)
        scorecard = _with_derived_overall(raw)

        assessment = Assessment(
            id=str(uuid.uuid4()),
            created_at=datetime.now(UTC),
            metadata=metadata,
            scorecard=scorecard,
            visual_analysis=analysis,
            context=context,
            image_sha256=image_sha256,
            provider_info={**provider_info, "cache_key": cache_key},
        )

        if self._repository is not None:
            await self._repository.add(assessment)
        return assessment

    async def get(self, assessment_id: str) -> Assessment | None:
        if self._repository is None:
            return None
        return await self._repository.get(assessment_id)

    async def history(self, *, limit: int = 20, offset: int = 0) -> list[Assessment]:
        if self._repository is None:
            return []
        return await self._repository.list(limit=limit, offset=offset)


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
