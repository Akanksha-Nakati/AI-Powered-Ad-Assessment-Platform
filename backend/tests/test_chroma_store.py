"""Tests against the real ChromaKnowledgeStore, with a stub embedding function.

These exist because the fake knowledge store implemented brand-scoped retrieval
correctly while the real adapter silently ignored brand_id entirely -- every
brand test passed against a fake that was more capable than the thing it stood
in for. Testing the adapter's own wiring is what closes that gap.

Embeddings are stubbed rather than called: the point is the store's routing and
filtering logic, not Google's vector quality.
"""

from __future__ import annotations

import hashlib

import pytest

from backend.app.infra.rag.chroma_store import ChromaKnowledgeStore


class StubEmbeddings:
    """Deterministic hash-based vectors -- no network, stable across runs."""

    DIMS = 32

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [digest[i % len(digest)] / 255.0 for i in range(self.DIMS)]


@pytest.fixture
def store(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    # ensure_ready also seeds AIDA.md and friends into this directory, so the
    # global collection is this file plus the shipped corpus.
    (docs / "Global_Guidance.md").write_text(
        "Use explicit verbs in calls to action.\n\nKeep the palette limited.",
        encoding="utf-8",
    )

    s = ChromaKnowledgeStore(
        docs_path=docs,
        persist_path=tmp_path / "chroma",
        embedding_model="stub",
        google_api_key="unused",
        chunk_size=200,
        chunk_overlap=0,
        retrieval_k=4,
    )
    # Substitute the embedding function the adapter would construct.
    monkeypatch.setattr(
        "langchain_google_genai.GoogleGenerativeAIEmbeddings",
        lambda **kwargs: StubEmbeddings(),
    )
    return s


async def test_retrieve_without_brand_returns_global_guidance(store):
    await store.ensure_ready()

    chunks = await store.retrieve("call to action", k=2)

    assert chunks
    assert all(c.brand_id is None for c in chunks)


async def test_brand_documents_are_retrieved_alongside_global(store):
    """The regression: retrieve() ignored brand_id, so brand chunks never
    reached the scorer even though ingestion had stored them."""
    await store.ensure_ready()
    count = await store.ingest_brand_document(
        "brand-1", "voice.md", "Never use exclamation marks. Our accent is coral."
    )
    assert count == 1

    chunks = await store.retrieve("brand voice rules", k=4, brand_id="brand-1")

    sources = {c.source for c in chunks}
    assert "voice.md" in sources, "brand guidance must be retrieved"
    # ensure_marketing_docs seeds the global corpus, so "global" here means any
    # non-brand source rather than one specific filename.
    assert sources - {"voice.md"}, "global guidance must survive alongside it"


async def test_brand_filter_excludes_other_brands(store):
    await store.ensure_ready()
    await store.ingest_brand_document("brand-1", "one.md", "Brand one voice rules.")
    await store.ingest_brand_document("brand-2", "two.md", "Brand two voice rules.")

    chunks = await store.retrieve("voice rules", k=4, brand_id="brand-1")

    assert "two.md" not in {c.source for c in chunks}


async def test_reingesting_replaces_chunks_rather_than_duplicating(store):
    await store.ensure_ready()
    await store.ingest_brand_document("brand-1", "voice.md", "First version.")
    await store.ingest_brand_document("brand-1", "voice.md", "Second version.")

    assert store._brand_store._collection.count() == 1


async def test_removing_a_brand_drops_only_its_chunks(store):
    await store.ensure_ready()
    await store.ingest_brand_document("brand-1", "one.md", "Brand one rules.")
    await store.ingest_brand_document("brand-2", "two.md", "Brand two rules.")

    await store.remove_brand("brand-1")

    remaining = await store.retrieve("rules", k=4, brand_id="brand-2")
    assert "one.md" not in {c.source for c in remaining}
    assert "two.md" in {c.source for c in remaining}


async def test_is_ready_requires_both_collections(store):
    assert store.is_ready is False
    await store.ensure_ready()
    assert store.is_ready is True
