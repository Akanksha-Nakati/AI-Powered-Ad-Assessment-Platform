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
    Assessment,
    Brand,
    KnowledgeDocument,
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
        """Retrieve guidance, merging global best practice with brand-specific
        documents when ``brand_id`` is given.

        Raises:
            KnowledgeStoreUnavailable: the store is not ready or failed.
        """
        ...

    async def ingest_brand_document(
        self, brand_id: str, filename: str, content: str
    ) -> int:
        """Chunk and embed one brand document. Returns the chunk count."""
        ...

    async def remove_brand(self, brand_id: str) -> None:
        """Drop every chunk belonging to a brand."""
        ...


@runtime_checkable
class BlobStore(Protocol):
    """Content-addressed storage for uploaded images."""

    async def put(self, data: bytes, media_type: str) -> str:
        """Store bytes and return their sha256 digest.

        Content addressing means storing the same ad twice costs one copy, and
        the digest doubles as the assessment cache key.
        """
        ...

    async def get(self, digest: str) -> bytes | None:
        """Return the stored bytes, or None if the digest is unknown."""
        ...


@runtime_checkable
class AssessmentRepository(Protocol):
    """Persistence for completed assessments."""

    async def add(self, assessment: Assessment) -> None: ...

    async def get(self, assessment_id: str) -> Assessment | None: ...

    async def list_recent(
        self, *, limit: int = 20, offset: int = 0
    ) -> list[Assessment]:
        """Most recent first."""
        ...

    async def find_cached(self, cache_key: str) -> Assessment | None:
        """Return a previous assessment for an identical request, if any."""
        ...

    async def set_external_ad_id(
        self, assessment_id: str, external_ad_id: str | None
    ) -> Assessment:
        """Tag (or untag, with None) an assessment with its warehouse identifier.

        Raises:
            NotFoundError: no assessment has this id.
            ConflictError: a *different* assessment already holds this id.
                Re-setting the same assessment's own tag is idempotent.
        """
        ...

    async def list_by_external_ids(self, external_ad_ids: list[str]) -> list[Assessment]:
        """Assessments tagged with any of the given warehouse identifiers."""
        ...


@runtime_checkable
class BrandRepository(Protocol):
    """Persistence for brands and the documents ingested for them."""

    async def create(self, name: str) -> Brand: ...

    async def get(self, brand_id: str) -> Brand | None: ...

    async def get_by_name(self, name: str) -> Brand | None: ...

    async def list_brands(self) -> list[Brand]: ...

    async def delete(self, brand_id: str) -> bool: ...

    async def add_document(
        self,
        brand_id: str,
        filename: str,
        content: str,
        content_sha256: str,
        chunk_count: int,
    ) -> KnowledgeDocument: ...

    async def list_documents(self, brand_id: str) -> list[KnowledgeDocument]: ...

    async def find_document_by_hash(
        self, brand_id: str, content_sha256: str
    ) -> KnowledgeDocument | None:
        """Used to skip re-embedding a document that has not changed."""
        ...
