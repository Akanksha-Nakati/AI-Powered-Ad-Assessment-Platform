"""Ports: the contracts infrastructure must satisfy.

Services depend on these Protocols and never import an SDK. That is what makes
the pipeline runnable in tests without network access or API keys -- the fakes
in tests/fakes.py satisfy exactly these signatures.

Runtime-checkable so the composition root can assert wiring at startup rather
than failing on the first request.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    Assessment,
    Brand,
    DataSourceConnection,
    KnowledgeDocument,
    PerformanceMetric,
    RawMetricRow,
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

    async def list_tagged(self) -> list[Assessment]:
        """Every assessment with a non-null external_ad_id, regardless of
        connection. Used to report assessments tagged but absent from one
        particular warehouse pull -- distinct from list_by_external_ids,
        which only looks up ids you already know to ask about."""
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


@runtime_checkable
class PerformanceSource(Protocol):
    """Runs a user-supplied query against their own SQL data warehouse.

    Takes the connection URI and query as call arguments rather than adapter
    state, because each DataSourceConnection has its own distinct connection
    string -- the same shape as KnowledgeStore.retrieve(query, k, brand_id)
    taking "which scope" as a parameter instead of one instance per brand.
    """

    async def test_connection(self, connection_uri: str, query: str) -> None:
        """
        Raises:
            WarehouseConnectionError: could not connect, or no driver for
                this connection string's dialect is installed.
            WarehouseQueryError: the query is rejected (not a single SELECT)
                or fails to execute.
        """
        ...

    async def fetch_metrics(self, connection_uri: str, query: str) -> list[RawMetricRow]:
        """
        Raises:
            WarehouseConnectionError: could not connect.
            WarehouseQueryError: the query failed, or its result does not
                contain the required columns.
        """
        ...


@runtime_checkable
class DataSourceRepository(Protocol):
    """Persistence for data-warehouse connections and the metrics pulled from
    them. Mirrors BrandRepository's shape."""

    async def create(
        self, name: str, dialect: str, connection_uri: str, query: str
    ) -> DataSourceConnection: ...

    async def get(self, connection_id: str) -> DataSourceConnection | None: ...

    async def list_connections(self) -> list[DataSourceConnection]: ...

    async def delete(self, connection_id: str) -> bool: ...

    async def get_connection_secret(
        self, connection_id: str
    ) -> tuple[str, str] | None:
        """Decrypted (connection_uri, query). Service-only -- never reachable
        from the API layer, and the connection is never modeled with these
        fields for exactly that reason."""
        ...

    async def record_test_result(
        self, connection_id: str, ok: bool, tested_at: datetime
    ) -> None: ...

    async def save_metrics(self, connection_id: str, rows: list[RawMetricRow]) -> int:
        """Replaces this connection's previous metrics with the new pull.
        Returns the row count saved."""
        ...

    async def list_metrics(self, connection_id: str) -> list[PerformanceMetric]: ...
