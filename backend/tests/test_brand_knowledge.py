"""Brand knowledge ingestion and brand-scoped retrieval."""

from __future__ import annotations

import pytest

from backend.app.domain.errors import ConflictError, NotFoundError
from backend.app.services.knowledge_service import KnowledgeService
from backend.tests.fakes import FakeBrandRepository, FakeKnowledgeStore

GUIDELINES = (
    "Our voice is plain and direct.\n\n"
    "Never use exclamation marks in headlines.\n\n"
    "The logo must appear in the lower-right corner."
)


def _upload(client, brand_id, content=GUIDELINES, filename="voice.md"):
    return client.post(
        f"/api/v1/brands/{brand_id}/documents",
        files={"document": (filename, content.encode(), "text/markdown")},
    )


# --- API -------------------------------------------------------------------


def test_create_and_list_brands(make_client):
    client, _ = make_client()

    created = client.post("/api/v1/brands", json={"name": "Acme"})
    assert created.status_code == 201
    assert created.json()["name"] == "Acme"

    listed = client.get("/api/v1/brands").json()
    assert [b["name"] for b in listed] == ["Acme"]


def test_duplicate_brand_name_is_409(make_client):
    client, _ = make_client()
    client.post("/api/v1/brands", json={"name": "Acme"})

    assert client.post("/api/v1/brands", json={"name": "Acme"}).status_code == 409


def test_upload_document_chunks_and_counts(make_client):
    knowledge = FakeKnowledgeStore()
    client, _ = make_client(knowledge=knowledge)
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]

    response = _upload(client, brand_id)

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "voice.md"
    assert body["chunk_count"] == 3
    assert knowledge.ingested == [(brand_id, "voice.md", 3)]


def test_reuploading_identical_content_skips_re_embedding(make_client):
    """Embedding costs money; identical bytes should not be paid for twice."""
    knowledge = FakeKnowledgeStore()
    client, _ = make_client(knowledge=knowledge)
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]

    first = _upload(client, brand_id).json()
    second = _upload(client, brand_id).json()

    assert first["id"] == second["id"]
    assert len(knowledge.ingested) == 1, "should only have embedded once"


def test_changed_content_is_re_embedded(make_client):
    knowledge = FakeKnowledgeStore()
    client, _ = make_client(knowledge=knowledge)
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]

    _upload(client, brand_id)
    _upload(client, brand_id, content="A totally different guideline.")

    assert len(knowledge.ingested) == 2


def test_upload_to_unknown_brand_is_404(make_client):
    client, _ = make_client()
    assert _upload(client, "nope").status_code == 404


def test_rejects_non_text_document(make_client):
    client, _ = make_client()
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]

    response = client.post(
        f"/api/v1/brands/{brand_id}/documents",
        files={"document": ("logo.png", b"\x89PNG", "image/png")},
    )
    assert response.status_code == 415


def test_rejects_non_utf8_document(make_client):
    client, _ = make_client()
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]

    response = client.post(
        f"/api/v1/brands/{brand_id}/documents",
        files={"document": ("notes.md", b"\xff\xfe\x00bad", "text/markdown")},
    )
    assert response.status_code == 400


def test_deleting_a_brand_drops_its_vectors(make_client):
    """An orphaned chunk would keep being cited for a brand that is gone."""
    knowledge = FakeKnowledgeStore()
    client, _ = make_client(knowledge=knowledge)
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]
    _upload(client, brand_id)

    assert client.delete(f"/api/v1/brands/{brand_id}").status_code == 204
    assert knowledge.removed_brands == [brand_id]
    assert client.get(f"/api/v1/brands/{brand_id}").status_code == 404


# --- the actual point ------------------------------------------------------


async def test_brand_guidance_reaches_the_scorer(make_client, png_bytes):
    """The whole feature is worthless if brand chunks never reach the judgement."""
    from backend.app.domain.models import AdMetadata
    from backend.tests.fakes import FakeScorer

    knowledge = FakeKnowledgeStore()
    scorer = FakeScorer()
    client, container = make_client(knowledge=knowledge, scorer=scorer)
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]
    _upload(client, brand_id)

    await container.assessments.assess(
        image=png_bytes,
        media_type="image/png",
        metadata=AdMetadata(
            platform="TikTok", industry="Ecommerce", ad_type="Story/Reel"
        ),
        brand_id=brand_id,
    )

    sources = [c.source for c in scorer.received_context]
    assert "voice.md" in sources, "brand guidance must be retrievable"
    assert any(
        c.source.endswith("_Best_Practices.md") or c.source.endswith("Psychology.md")
        for c in scorer.received_context
    ), "global best practice must still be present alongside brand guidance"


# --- service-level ---------------------------------------------------------


async def test_service_rejects_blank_brand_name():
    service = KnowledgeService(FakeBrandRepository(), FakeKnowledgeStore())

    with pytest.raises(ConflictError):
        await service.create_brand("   ")


async def test_service_raises_not_found_for_unknown_brand():
    service = KnowledgeService(FakeBrandRepository(), FakeKnowledgeStore())

    with pytest.raises(NotFoundError):
        await service.get_brand("missing")


def test_assess_endpoint_accepts_a_brand(make_client, png_bytes):
    knowledge = FakeKnowledgeStore()
    client, _ = make_client(knowledge=knowledge)
    brand_id = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]
    _upload(client, brand_id)

    response = client.post(
        "/api/v1/assessments",
        files={"ad_image": ("ad.png", png_bytes, "image/png")},
        data={
            "platform": "TikTok",
            "industry": "Ecommerce",
            "ad_type": "Story/Reel",
            "brand_id": brand_id,
        },
    )

    assert response.status_code == 201
    assert knowledge.retrieved_brand_ids == [brand_id]
    assert "voice.md" in [c["source"] for c in response.json()["context"]]


def test_assessments_for_different_brands_are_cached_separately(make_client, png_bytes):
    """The same creative judged against different guidelines is a different question."""
    from backend.tests.fakes import FakeVisionAnalyzer

    vision = FakeVisionAnalyzer()
    client, _ = make_client(vision=vision)
    acme = client.post("/api/v1/brands", json={"name": "Acme"}).json()["id"]
    globex = client.post("/api/v1/brands", json={"name": "Globex"}).json()["id"]

    form = {"platform": "TikTok", "industry": "Ecommerce", "ad_type": "Story/Reel"}
    for brand in (acme, globex):
        client.post(
            "/api/v1/assessments",
            files={"ad_image": ("ad.png", png_bytes, "image/png")},
            data={**form, "brand_id": brand},
        )

    assert len(vision.calls) == 2
