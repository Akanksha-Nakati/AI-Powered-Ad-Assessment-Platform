"""In-memory implementations of every port.

These satisfy the Protocols in app/domain/ports.py exactly, which is what lets
the entire assess pipeline run in tests with no network and no API keys -- the
thing the previous architecture made impossible.
"""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import (
    ConflictError,
    KnowledgeStoreUnavailable,
    NotFoundError,
)
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    Brand,
    KnowledgeDocument,
    RetrievedChunk,
    VisualAnalysis,
)

SAMPLE_ANALYSIS = VisualAnalysis(
    colors=["#0EA5E9", "#111827"],
    text="Save 30% this week",
    layout="Product left, headline right, CTA lower-right.",
    cta="Shop now",
    insights=["Strong contrast", "CTA competes with the price badge"],
)

SAMPLE_CHUNKS = [
    RetrievedChunk(text="Use explicit verbs such as 'Shop now'.",
                   source="CTA_Best_Practices.md", chunk=0),
    RetrievedChunk(text="Limit the palette to two primaries plus an accent.",
                   source="Color_Psychology.md", chunk=1),
]


class FakeVisionAnalyzer:
    def __init__(
        self, analysis: VisualAnalysis | None = None, error: Exception | None = None
    ):
        self._analysis = analysis or SAMPLE_ANALYSIS
        self._error = error
        self.calls: list[tuple[int, str]] = []

    async def analyze(self, image: bytes, media_type: str) -> VisualAnalysis:
        self.calls.append((len(image), media_type))
        if self._error:
            raise self._error
        return self._analysis


class FakeScorer:
    def __init__(
        self, scorecard: AdScorecard | None = None, error: Exception | None = None
    ):
        self._scorecard = scorecard or _full_scorecard()
        self._error = error
        self.received_context: list[RetrievedChunk] = []

    async def score(
        self,
        analysis: VisualAnalysis,
        context: list[RetrievedChunk],
        metadata: AdMetadata,
    ) -> AdScorecard:
        self.received_context = context
        if self._error:
            raise self._error
        return self._scorecard


class FakeKnowledgeStore:
    def __init__(self, chunks: list[RetrievedChunk] | None = None, ready: bool = True):
        self._chunks = chunks if chunks is not None else SAMPLE_CHUNKS
        self._ready = ready
        self.queries: list[str] = []
        self.retrieved_brand_ids: list[str | None] = []
        self.brand_chunks: dict[str, list[RetrievedChunk]] = {}
        self.ingested: list[tuple[str, str, int]] = []
        self.removed_brands: list[str] = []
        self.ensure_ready_calls = 0

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def ensure_ready(self) -> None:
        self.ensure_ready_calls += 1

    async def retrieve(
        self, query: str, k: int | None = None, brand_id: str | None = None
    ) -> list[RetrievedChunk]:
        if not self._ready:
            raise KnowledgeStoreUnavailable("fake store is not ready")
        self.queries.append(query)
        self.retrieved_brand_ids.append(brand_id)
        chunks = self._chunks[: k or len(self._chunks)]
        if brand_id is not None:
            chunks = self.brand_chunks.get(brand_id, []) + chunks
        return chunks

    async def ingest_brand_document(
        self, brand_id: str, filename: str, content: str
    ) -> int:
        if not self._ready:
            raise KnowledgeStoreUnavailable("fake store is not ready")
        chunks = [c for c in content.split("\n\n") if c.strip()]
        self.brand_chunks.setdefault(brand_id, []).extend(
            RetrievedChunk(text=c, source=filename, chunk=i, brand_id=brand_id)
            for i, c in enumerate(chunks)
        )
        self.ingested.append((brand_id, filename, len(chunks)))
        return len(chunks)

    async def remove_brand(self, brand_id: str) -> None:
        self.brand_chunks.pop(brand_id, None)
        self.removed_brands.append(brand_id)


def _full_scorecard(**overrides) -> AdScorecard:
    scores = dict.fromkeys(Criterion, 7.0)
    payload = {
        "scores": scores,
        "overall_score": 7.0,
        "feedback": "Solid creative with a clear offer.",
        "recommendations": ["Increase CTA contrast."],
        "citations": ["CTA_Best_Practices.md"],
    }
    payload.update(overrides)
    return AdScorecard(**payload)


class FakeBlobStore:
    """In-memory content-addressed store."""

    def __init__(self) -> None:
        self.blobs: dict[str, bytes] = {}
        self.media_types: dict[str, str] = {}

    async def put(self, data: bytes, media_type: str) -> str:
        import hashlib

        digest = hashlib.sha256(data).hexdigest()
        self.blobs[digest] = data
        self.media_types[digest] = media_type
        return digest

    async def get(self, digest: str) -> bytes | None:
        return self.blobs.get(digest)


class FakeAssessmentRepository:
    """In-memory repository preserving insertion order."""

    def __init__(self) -> None:
        self.saved: list = []
        self.by_cache_key: dict = {}

    async def add(self, assessment) -> None:
        self.saved.append(assessment)
        key = assessment.provider_info.get("cache_key")
        if key:
            self.by_cache_key[key] = assessment

    async def get(self, assessment_id: str):
        return next((a for a in self.saved if a.id == assessment_id), None)

    async def list_recent(self, *, limit: int = 20, offset: int = 0) -> list:
        newest_first = list(reversed(self.saved))
        return newest_first[offset : offset + limit]

    async def find_cached(self, cache_key: str):
        return self.by_cache_key.get(cache_key)

    async def set_external_ad_id(self, assessment_id: str, external_ad_id: str | None):
        assessment = await self.get(assessment_id)
        if assessment is None:
            raise NotFoundError(f"no assessment with id {assessment_id}")
        if external_ad_id is not None:
            collision = next(
                (
                    a
                    for a in self.saved
                    if a.external_ad_id == external_ad_id and a.id != assessment_id
                ),
                None,
            )
            if collision is not None:
                raise ConflictError(
                    f"assessment {collision.id} already uses external_ad_id "
                    f"{external_ad_id!r}"
                )
        updated = assessment.model_copy(update={"external_ad_id": external_ad_id})
        self.saved[self.saved.index(assessment)] = updated
        key = updated.provider_info.get("cache_key")
        if key:
            self.by_cache_key[key] = updated
        return updated

    async def list_by_external_ids(self, external_ad_ids: list[str]) -> list:
        wanted = set(external_ad_ids)
        return [a for a in self.saved if a.external_ad_id in wanted]


class FakeBrandRepository:
    """In-memory brand and document store."""

    def __init__(self) -> None:
        self.brands: dict[str, Brand] = {}
        self.documents: dict[str, list[KnowledgeDocument]] = {}
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter}"

    async def create(self, name: str) -> Brand:
        if any(b.name == name for b in self.brands.values()):
            raise ConflictError(f"a brand named {name!r} already exists")
        brand = Brand(id=self._next_id("brand"), name=name, created_at=datetime.now(UTC))
        self.brands[brand.id] = brand
        return brand

    async def get(self, brand_id: str) -> Brand | None:
        brand = self.brands.get(brand_id)
        if brand is None:
            return None
        return brand.model_copy(
            update={"document_count": len(self.documents.get(brand_id, []))}
        )

    async def get_by_name(self, name: str) -> Brand | None:
        return next((b for b in self.brands.values() if b.name == name), None)

    async def list_brands(self) -> list[Brand]:
        return sorted(self.brands.values(), key=lambda b: b.name)

    async def delete(self, brand_id: str) -> bool:
        self.documents.pop(brand_id, None)
        return self.brands.pop(brand_id, None) is not None

    async def add_document(
        self,
        brand_id: str,
        filename: str,
        content: str,
        content_sha256: str,
        chunk_count: int,
    ) -> KnowledgeDocument:
        docs = self.documents.setdefault(brand_id, [])
        docs[:] = [d for d in docs if d.filename != filename]
        doc = KnowledgeDocument(
            id=self._next_id("doc"),
            brand_id=brand_id,
            filename=filename,
            content_sha256=content_sha256,
            chunk_count=chunk_count,
            created_at=datetime.now(UTC),
        )
        docs.append(doc)
        return doc

    async def list_documents(self, brand_id: str) -> list[KnowledgeDocument]:
        return sorted(self.documents.get(brand_id, []), key=lambda d: d.filename)

    async def find_document_by_hash(
        self, brand_id: str, content_sha256: str
    ) -> KnowledgeDocument | None:
        return next(
            (
                d
                for d in self.documents.get(brand_id, [])
                if d.content_sha256 == content_sha256
            ),
            None,
        )
