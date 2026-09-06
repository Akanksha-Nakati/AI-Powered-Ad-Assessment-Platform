"""End-to-end pipeline tests -- no network, no API keys."""

from __future__ import annotations

import pytest

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import InvalidProviderOutput, ProviderError
from backend.app.domain.models import AdMetadata, VisualAnalysis
from backend.app.services.assessment_service import build_retrieval_query
from backend.tests.fakes import (
    FakeKnowledgeStore,
    FakeScorer,
    FakeVisionAnalyzer,
    _full_scorecard,
)

FORM = {"platform": "TikTok", "industry": "Ecommerce", "ad_type": "Story/Reel"}


def _post(client, png_bytes):
    return client.post(
        "/api/v1/assessments",
        files={"ad_image": ("ad.png", png_bytes, "image/png")},
        data=FORM,
    )


def test_full_assessment_returns_all_six_criteria(make_client, png_bytes):
    client, _ = make_client()
    response = _post(client, png_bytes)

    assert response.status_code == 201
    body = response.json()
    assert set(body["scorecard"]["scores"]) == {c.value for c in Criterion}
    assert body["metadata"]["platform"] == "TikTok"
    assert body["image_sha256"]
    assert body["context"], "retrieved guidance should be returned for citation"


def test_retrieved_context_reaches_the_scorer(make_client, png_bytes):
    """The RAG half of 'RAG-powered' has to actually reach the judgement."""
    scorer = FakeScorer()
    knowledge = FakeKnowledgeStore()
    client, _ = make_client(scorer=scorer, knowledge=knowledge)

    _post(client, png_bytes)

    assert knowledge.queries, "the store should have been queried"
    assert scorer.received_context, "retrieved chunks must be passed to the scorer"
    assert scorer.received_context[0].source == "CTA_Best_Practices.md"


def test_overall_score_is_derived_not_trusted(make_client, png_bytes):
    """A provider that contradicts its own numbers must not set the headline."""
    lying = _full_scorecard(
        scores=dict.fromkeys(Criterion, 4.0),
        overall_score=9.9,  # inconsistent with the per-criterion scores
    )
    client, _ = make_client(scorer=FakeScorer(scorecard=lying))

    body = _post(client, png_bytes).json()

    assert body["scorecard"]["overall_score"] == 4.0


def test_malformed_provider_output_is_502_not_an_empty_scorecard(make_client, png_bytes):
    """The regression that motivated the rewrite.

    The old code caught JSONDecodeError and returned empty scores, so a broken
    provider looked to the user like an ad that scored zero on everything.
    """
    client, _ = make_client(
        scorer=FakeScorer(error=InvalidProviderOutput("not a scorecard"))
    )

    response = _post(client, png_bytes)

    assert response.status_code == 502
    assert response.json()["error"] == "InvalidProviderOutput"
    assert "scorecard" not in response.json()


def test_provider_failure_does_not_leak_internals(make_client, png_bytes):
    client, _ = make_client(
        vision=FakeVisionAnalyzer(error=ProviderError("api key sk-secret-123 rejected"))
    )

    response = _post(client, png_bytes)

    assert response.status_code == 502
    assert "sk-secret-123" not in response.text


def test_knowledge_store_not_ready_is_503(make_client, png_bytes):
    client, _ = make_client(knowledge=FakeKnowledgeStore(ready=False))

    assert _post(client, png_bytes).status_code == 503


@pytest.mark.parametrize(
    "content_type,expected",
    [("image/png", 201), ("application/pdf", 415), ("text/html", 415)],
)
def test_rejects_non_image_uploads(make_client, png_bytes, content_type, expected):
    client, _ = make_client()
    response = client.post(
        "/api/v1/assessments",
        files={"ad_image": ("ad", png_bytes, content_type)},
        data=FORM,
    )
    assert response.status_code == expected


def test_rejects_empty_upload(make_client):
    client, _ = make_client()
    response = client.post(
        "/api/v1/assessments",
        files={"ad_image": ("ad.png", b"", "image/png")},
        data=FORM,
    )
    assert response.status_code == 400


def test_retrieval_query_includes_placement_and_creative():
    query = build_retrieval_query(
        VisualAnalysis(cta="Book a demo", layout="centred", text="Try free"),
        AdMetadata(platform="LinkedIn", industry="SaaS", ad_type="Banner"),
    )
    assert "LinkedIn" in query and "SaaS" in query and "Banner" in query
    assert "Book a demo" in query
