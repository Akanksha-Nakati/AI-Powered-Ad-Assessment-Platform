"""Compare several variants of an ad and rank them.

Uploading three variants means six model calls, so they are issued
concurrently rather than in sequence -- which is only possible because the
provider adapters are genuinely async. A semaphore bounds the fan-out so a
large upload cannot open an unbounded number of provider connections or blow
through a rate limit in one burst.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from backend.app.domain.errors import ProviderError
from backend.app.domain.models import (
    AdMetadata,
    Assessment,
    Comparison,
    ComparisonEntry,
)
from backend.app.services.assessment_service import AssessmentService

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENCY = 4


class ComparisonService:
    def __init__(
        self,
        assessments: AssessmentService,
        *,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    ) -> None:
        self._assessments = assessments
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def compare(
        self,
        variants: list[tuple[str, bytes, str]],
        metadata: AdMetadata,
        *,
        brand_id: str | None = None,
    ) -> Comparison:
        """Assess every variant, then rank by overall score.

        Args:
            variants: (label, image bytes, media type) per variant.
        """
        results = await asyncio.gather(
            *(
                self._assess_one(label, image, media_type, metadata, brand_id)
                for label, image, media_type in variants
            ),
            return_exceptions=True,
        )

        scored: list[tuple[str, Assessment]] = []
        failures: list[BaseException] = []
        for outcome in results:
            if isinstance(outcome, BaseException):
                failures.append(outcome)
            else:
                scored.append(outcome)

        if not scored:
            # Every variant failed: there is no partial result worth returning.
            raise failures[0] if failures else ProviderError("no variants were scored")
        if failures:
            # A ranking of the survivors is still useful; note what was lost.
            logger.warning(
                "%d of %d variants failed to score", len(failures), len(variants)
            )

        scored.sort(key=lambda pair: pair[1].scorecard.overall_score, reverse=True)
        return Comparison(
            id=str(uuid.uuid4()),
            created_at=datetime.now(UTC),
            metadata=metadata,
            entries=[
                ComparisonEntry(rank=index, label=label, assessment=assessment)
                for index, (label, assessment) in enumerate(scored, start=1)
            ],
        )

    async def _assess_one(
        self,
        label: str,
        image: bytes,
        media_type: str,
        metadata: AdMetadata,
        brand_id: str | None,
    ) -> tuple[str, Assessment]:
        async with self._semaphore:
            assessment = await self._assessments.assess(
                image=image,
                media_type=media_type,
                metadata=metadata,
                brand_id=brand_id,
            )
        return label, assessment
