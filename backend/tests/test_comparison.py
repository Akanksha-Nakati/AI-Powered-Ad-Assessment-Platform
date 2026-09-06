"""Variant comparison: ranking, concurrency, and partial failure."""

from __future__ import annotations

import asyncio

import pytest

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import ProviderError
from backend.app.domain.models import AdMetadata
from backend.app.services.comparison_service import ComparisonService
from backend.tests.fakes import _full_scorecard

FORM = {"platform": "TikTok", "industry": "Ecommerce", "ad_type": "Story/Reel"}
METADATA = AdMetadata(**FORM)


def _variants(png_bytes, n=3):
    return [
        ("ad_images", (f"variant-{i}.png", png_bytes + bytes([i]), "image/png"))
        for i in range(n)
    ]


def test_ranks_variants_best_first(make_client, png_bytes):
    """The point of the feature: which of these should I actually run?"""
    from backend.tests.fakes import FakeScorer

    scores = iter([5.0, 9.0, 7.0])

    class RankingScorer(FakeScorer):
        async def score(self, analysis, context, metadata):
            value = next(scores)
            return _full_scorecard(scores=dict.fromkeys(Criterion, value))

    client, _ = make_client(scorer=RankingScorer())

    response = client.post(
        "/api/v1/comparisons", files=_variants(png_bytes), data=FORM
    )

    assert response.status_code == 201
    entries = response.json()["entries"]
    assert [e["rank"] for e in entries] == [1, 2, 3]
    overall = [e["assessment"]["scorecard"]["overall_score"] for e in entries]
    assert overall == sorted(overall, reverse=True)
    assert overall[0] == 9.0
    assert entries[0]["label"] == "variant-1.png"


def test_requires_at_least_two_variants(make_client, png_bytes):
    client, _ = make_client()
    response = client.post(
        "/api/v1/comparisons", files=_variants(png_bytes, 1), data=FORM
    )
    assert response.status_code == 422


def test_rejects_too_many_variants(make_client, png_bytes):
    client, _ = make_client()
    response = client.post(
        "/api/v1/comparisons", files=_variants(png_bytes, 6), data=FORM
    )
    assert response.status_code == 422


def test_rejects_a_non_image_variant(make_client, png_bytes):
    client, _ = make_client()
    files = _variants(png_bytes, 2)
    files.append(("ad_images", ("notes.pdf", b"%PDF", "application/pdf")))

    response = client.post("/api/v1/comparisons", files=files, data=FORM)

    assert response.status_code == 415
    assert "notes.pdf" in response.json()["detail"]


# --- service-level ---------------------------------------------------------


class _SlowService:
    """Stands in for AssessmentService, recording overlap."""

    def __init__(self, delay: float = 0.05, fail_on: set[str] | None = None):
        self.delay = delay
        self.fail_on = fail_on or set()
        self.in_flight = 0
        self.peak_in_flight = 0

    async def assess(self, *, image, media_type, metadata, brand_id=None):
        from datetime import UTC, datetime

        from backend.app.domain.models import Assessment
        from backend.tests.fakes import SAMPLE_ANALYSIS

        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            marker = image.decode("latin-1")
            if marker in self.fail_on:
                raise ProviderError(f"variant {marker} failed")
            return Assessment(
                id=f"id-{marker}",
                created_at=datetime.now(UTC),
                metadata=metadata,
                scorecard=_full_scorecard(
                    scores=dict.fromkeys(Criterion, float(len(marker)))
                ),
                visual_analysis=SAMPLE_ANALYSIS,
                context=[],
            )
        finally:
            self.in_flight -= 1


async def test_variants_are_assessed_concurrently():
    """Sequential fan-out would make comparing five variants unusably slow."""
    inner = _SlowService(delay=0.05)
    service = ComparisonService(inner, max_concurrency=4)  # type: ignore[arg-type]
    variants = [(f"v{i}", b"x" * (i + 1), "image/png") for i in range(4)]

    loop = asyncio.get_running_loop()
    started = loop.time()
    await service.compare(variants, METADATA)
    elapsed = loop.time() - started

    assert inner.peak_in_flight > 1, "variants must overlap"
    assert elapsed < 0.05 * 4 * 0.75, "should be concurrent, not sequential"


async def test_concurrency_is_bounded():
    """An unbounded fan-out would hit provider rate limits in one burst."""
    inner = _SlowService(delay=0.02)
    service = ComparisonService(inner, max_concurrency=2)  # type: ignore[arg-type]
    variants = [(f"v{i}", b"x" * (i + 1), "image/png") for i in range(5)]

    await service.compare(variants, METADATA)

    assert inner.peak_in_flight <= 2


async def test_one_failing_variant_still_ranks_the_rest():
    """A partial ranking is useful; discarding everything is not."""
    inner = _SlowService(delay=0, fail_on={"xx"})
    service = ComparisonService(inner, max_concurrency=4)  # type: ignore[arg-type]
    variants = [(f"v{i}", b"x" * (i + 1), "image/png") for i in range(3)]

    comparison = await service.compare(variants, METADATA)

    assert len(comparison.entries) == 2
    assert [e.rank for e in comparison.entries] == [1, 2]


async def test_all_variants_failing_raises():
    inner = _SlowService(delay=0, fail_on={"x", "xx"})
    service = ComparisonService(inner, max_concurrency=4)  # type: ignore[arg-type]
    variants = [(f"v{i}", b"x" * (i + 1), "image/png") for i in range(2)]

    with pytest.raises(ProviderError):
        await service.compare(variants, METADATA)
