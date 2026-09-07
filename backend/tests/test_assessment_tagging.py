"""Tagging an assessment with its identifier in the user's own data warehouse.

This is the join key the performance-correlation feature depends on: nothing
in a warehouse pull can match one of our assessments without it.
"""

from __future__ import annotations

import pytest

from backend.app.domain.models import AdMetadata
from backend.app.infra.db.repositories import SqlAssessmentRepository
from backend.app.infra.db.session import (
    create_all,
    create_engine,
    create_session_factory,
)
from backend.tests.fakes import SAMPLE_ANALYSIS, SAMPLE_CHUNKS, _full_scorecard

FORM = {"platform": "TikTok", "industry": "Ecommerce", "ad_type": "Story/Reel"}


def _post(client, png_bytes, **overrides):
    data = {**FORM, **overrides}
    return client.post(
        "/api/v1/assessments",
        files={"ad_image": ("ad.png", png_bytes, "image/png")},
        data=data,
    )


def _patch(client, assessment_id, external_ad_id):
    return client.patch(
        f"/api/v1/assessments/{assessment_id}",
        json={"external_ad_id": external_ad_id},
    )


# --- API ---------------------------------------------------------------


def test_tag_an_assessment(make_client, png_bytes):
    client, _ = make_client()
    assessment_id = _post(client, png_bytes).json()["id"]

    tagged = _patch(client, assessment_id, "campaign-42")
    assert tagged.status_code == 200
    assert tagged.json()["external_ad_id"] == "campaign-42"

    fetched = client.get(f"/api/v1/assessments/{assessment_id}").json()
    assert fetched["external_ad_id"] == "campaign-42"


def test_tagging_an_unknown_assessment_is_404(make_client):
    client, _ = make_client()
    response = _patch(client, "no-such-id", "campaign-42")
    assert response.status_code == 404


def test_tagging_a_second_assessment_with_the_same_id_is_409(make_client, png_bytes):
    client, _ = make_client()
    first = _post(client, png_bytes).json()["id"]
    second = _post(client, png_bytes, platform="Facebook/IG").json()["id"]

    assert _patch(client, first, "campaign-42").status_code == 200
    conflict = _patch(client, second, "campaign-42")
    assert conflict.status_code == 409


def test_retagging_the_same_assessment_is_idempotent(make_client, png_bytes):
    client, _ = make_client()
    assessment_id = _post(client, png_bytes).json()["id"]

    assert _patch(client, assessment_id, "campaign-42").status_code == 200
    again = _patch(client, assessment_id, "campaign-42")
    assert again.status_code == 200
    assert again.json()["external_ad_id"] == "campaign-42"


def test_clearing_a_tag_with_null(make_client, png_bytes):
    client, _ = make_client()
    assessment_id = _post(client, png_bytes).json()["id"]
    _patch(client, assessment_id, "campaign-42")

    cleared = _patch(client, assessment_id, None)
    assert cleared.status_code == 200
    assert cleared.json()["external_ad_id"] is None


def test_tagging_does_not_change_the_cache_key(make_client, png_bytes):
    """Tagging must never invalidate the cached scorecard -- it's metadata
    about the ad's identity elsewhere, not about how it was scored."""
    client, _ = make_client()
    before = _post(client, png_bytes).json()
    assessment_id = before["id"]

    _patch(client, assessment_id, "campaign-42")

    after_resubmit = _post(client, png_bytes).json()
    assert after_resubmit["id"] == assessment_id, "still the same cached assessment"
    assert after_resubmit["external_ad_id"] == "campaign-42", "the tag survived"


# --- the real repository -------------------------------------------------


@pytest.fixture
async def sql_repo(tmp_path):
    engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await create_all(engine)
    yield SqlAssessmentRepository(create_session_factory(engine))
    await engine.dispose()


async def _make_assessment(**overrides):
    from datetime import UTC, datetime

    from backend.app.domain.models import Assessment

    payload = {
        "id": overrides.pop("id", "11111111-1111-1111-1111-111111111111"),
        "created_at": datetime.now(UTC),
        "metadata": AdMetadata(platform="TikTok", industry="SaaS", ad_type="Banner"),
        "scorecard": _full_scorecard(),
        "visual_analysis": SAMPLE_ANALYSIS,
        "context": SAMPLE_CHUNKS,
        "image_sha256": "a" * 64,
        "provider_info": {"cache_key": overrides.pop("cache_key", "key-1")},
    }
    payload.update(overrides)
    return Assessment(**payload)


async def test_sql_set_external_ad_id(sql_repo):
    await sql_repo.add(await _make_assessment())

    tagged = await sql_repo.set_external_ad_id(
        "11111111-1111-1111-1111-111111111111", "campaign-42"
    )
    assert tagged.external_ad_id == "campaign-42"


async def test_sql_unique_constraint_backs_the_service_check(sql_repo):
    """The service does a check-then-set; this proves the DB's own unique
    index would catch a collision even if that check were ever skipped."""
    await sql_repo.add(await _make_assessment())
    await sql_repo.add(
        await _make_assessment(
            id="22222222-2222-2222-2222-222222222222", cache_key="key-2"
        )
    )
    await sql_repo.set_external_ad_id(
        "11111111-1111-1111-1111-111111111111", "campaign-42"
    )

    from backend.app.domain.errors import ConflictError

    with pytest.raises(ConflictError):
        await sql_repo.set_external_ad_id(
            "22222222-2222-2222-2222-222222222222", "campaign-42"
        )


async def test_sql_list_by_external_ids(sql_repo):
    await sql_repo.add(await _make_assessment())
    await sql_repo.add(
        await _make_assessment(
            id="22222222-2222-2222-2222-222222222222", cache_key="key-2"
        )
    )
    await sql_repo.set_external_ad_id(
        "11111111-1111-1111-1111-111111111111", "campaign-42"
    )

    matched = await sql_repo.list_by_external_ids(["campaign-42", "no-such-id"])
    assert [a.id for a in matched] == ["11111111-1111-1111-1111-111111111111"]


async def test_sql_list_by_external_ids_empty_input(sql_repo):
    assert await sql_repo.list_by_external_ids([]) == []
