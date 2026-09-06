"""Ports: the contracts infrastructure must satisfy.

Services depend on these Protocols and never import an SDK. That is what makes
the pipeline runnable in tests without network access or API keys -- the fakes
in tests/fakes.py satisfy exactly these signatures.

Runtime-checkable so the composition root can assert wiring at startup rather
than failing on the first request.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    RetrievedChunk,
    VisualAnalysis,
)


@runtime_checkable
class VisionAnalyzer(Protocol):
    """Turns an ad image into a structured description."""

    async def analyze(self, image: bytes, media_type: str) -> VisualAnalysis:
        """
        Raises:
            ProviderError: the provider failed or was unreachable.
            InvalidProviderOutput: the reply did not match VisualAnalysis.
        """
        ...


@runtime_checkable
class Scorer(Protocol):
    """Judges an ad against retrieved guidance and returns a scorecard."""

    async def score(
        self,
        analysis: VisualAnalysis,
        context: list[RetrievedChunk],
        metadata: AdMetadata,
    ) -> AdScorecard:
        """
        Raises:
            ProviderError: the provider failed or was unreachable.
            InvalidProviderOutput: the reply did not match AdScorecard.
        """
        ...


@runtime_checkable
class KnowledgeStore(Protocol):
    """Retrieval over marketing guidance, optionally scoped to one brand."""

    async def ensure_ready(self) -> None:
        """Build or open the store. Called once at startup, not per request."""
        ...

    async def retrieve(
        self,
        query: str,
        k: int | None = None,
        brand_id: str | None = None,
    ) -> list[RetrievedChunk]:
        """
        Raises:
            KnowledgeStoreUnavailable: the store is not ready or failed.
        """
        ...
