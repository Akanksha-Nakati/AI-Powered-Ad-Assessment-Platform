"""In-memory implementations of every port.

These satisfy the Protocols in app/domain/ports.py exactly, which is what lets
the entire assess pipeline run in tests with no network and no API keys -- the
thing the previous architecture made impossible.
"""

from __future__ import annotations

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import KnowledgeStoreUnavailable
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
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
        self.ensure_ready_calls = 0

    async def ensure_ready(self) -> None:
        self.ensure_ready_calls += 1

    async def retrieve(
        self, query: str, k: int | None = None, brand_id: str | None = None
    ) -> list[RetrievedChunk]:
        if not self._ready:
            raise KnowledgeStoreUnavailable("fake store is not ready")
        self.queries.append(query)
        return self._chunks[: k or len(self._chunks)]


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

    async def list(self, *, limit: int = 20, offset: int = 0) -> list:
        newest_first = list(reversed(self.saved))
        return newest_first[offset : offset + limit]

    async def find_cached(self, cache_key: str):
        return self.by_cache_key.get(cache_key)
