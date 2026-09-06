"""Caching, history, and the real SQLAlchemy repository."""

from __future__ import annotations

import pytest

from backend.app.domain.models import AdMetadata
from backend.app.infra.db.repositories import SqlAssessmentRepository
from backend.app.infra.db.session import (
    create_all,
    create_engine,
    create_session_factory,
)
from backend.app.infra.storage.local_blob import LocalBlobStore, digest_of
from backend.app.services.assessment_service import build_cache_key
from backend.tests.fakes import FakeBlobStore

FORM = {"platform": "TikTok", "industry": "Ecommerce", "ad_type": "Story/Reel"}


def _post(client, png_bytes, **overrides):
    data = {**FORM, **overrides}
    return client.post(
        "/api/v1/assessments",
        files={"ad_image": ("ad.png", png_bytes, "image/png")},
        data=data,
    )


# --- caching ---------------------------------------------------------------


def test_identical_resubmission_is_served_from_cache(make_client, png_bytes):
    """Two model calls per assessment is the expensive part; don't pay twice."""
    from backend.tests.fakes import FakeVisionAnalyzer

    vision = FakeVisionAnalyzer()
    client, _ = make_client(vision=vision)

    first = _post(client, png_bytes).json()
    second = _post(client, png_bytes).json()

    assert first["id"] == second["id"], "the cached assessment should be returned"
    assert len(vision.calls) == 1, "the vision model should only have been called once"


def test_changing_placement_busts_the_cache(make_client, png_bytes):
    from backend.tests.fakes import FakeVisionAnalyzer

    vision = FakeVisionAnalyzer()
    client, _ = make_client(vision=vision)

    _post(client, png_bytes)
    _post(client, png_bytes, platform="LinkedIn")

    assert len(vision.calls) == 2, "a different placement is a different question"


def test_cache_key_covers_model_and_prompt_version():
    """A prompt edit or model swap must not serve the previous verdict."""
    metadata = AdMetadata(platform="TikTok", industry="Ecommerce", ad_type="Banner")
    base = build_cache_key("abc", metadata, {"prompt_version": "v1"}, None)

    assert base != build_cache_key("abc", metadata, {"prompt_version": "v2"}, None)
    assert base != build_cache_key(
        "abc", metadata, {"prompt_version": "v1", "scoring_model": "x"}, None
    )
    assert base != build_cache_key(
        "different-image", metadata, {"prompt_version": "v1"}, None
    )
    assert base == build_cache_key("abc", metadata, {"prompt_version": "v1"}, None)


# --- history ---------------------------------------------------------------


def test_history_returns_most_recent_first(make_client, png_bytes):
    client, _ = make_client()
    _post(client, png_bytes, platform="TikTok")
    _post(client, png_bytes, platform="LinkedIn")

    history = client.get("/api/v1/assessments").json()

    assert len(history) == 2
    assert history[0]["metadata"]["platform"] == "LinkedIn"


def test_history_paginates(make_client, png_bytes):
    client, _ = make_client()
    for platform in ("TikTok", "LinkedIn", "YouTube"):
        _post(client, png_bytes, platform=platform)

    page = client.get("/api/v1/assessments", params={"limit": 2, "offset": 1}).json()

    assert len(page) == 2
    assert page[0]["metadata"]["platform"] == "LinkedIn"


def test_get_assessment_by_id(make_client, png_bytes):
    client, _ = make_client()
    created = _post(client, png_bytes).json()

    fetched = client.get(f"/api/v1/assessments/{created['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_unknown_assessment_is_404(make_client):
    client, _ = make_client()
    assert client.get("/api/v1/assessments/does-not-exist").status_code == 404


def test_upload_is_stored_content_addressed(make_client, png_bytes):
    blobs = FakeBlobStore()
    client, _ = make_client(blobs=blobs)

    body = _post(client, png_bytes).json()

    assert body["image_sha256"] in blobs.blobs
    assert blobs.blobs[body["image_sha256"]] == png_bytes


# --- the real repository ---------------------------------------------------


@pytest.fixture
async def sql_repo(tmp_path):
    engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await create_all(engine)
    yield SqlAssessmentRepository(create_session_factory(engine))
    await engine.dispose()


async def _make_assessment(**overrides):
    from datetime import UTC, datetime

    from backend.app.domain.models import Assessment
    from backend.tests.fakes import SAMPLE_ANALYSIS, SAMPLE_CHUNKS, _full_scorecard

    payload = {
        "id": "11111111-1111-1111-1111-111111111111",
        "created_at": datetime.now(UTC),
        "metadata": AdMetadata(platform="TikTok", industry="SaaS", ad_type="Banner"),
        "scorecard": _full_scorecard(),
        "visual_analysis": SAMPLE_ANALYSIS,
        "context": SAMPLE_CHUNKS,
        "image_sha256": "a" * 64,
        "provider_info": {"cache_key": "key-1", "scoring_model": "claude-opus-5"},
    }
    payload.update(overrides)
    return Assessment(**payload)


async def test_sql_roundtrip_preserves_the_domain_model(sql_repo):
    original = await _make_assessment()

    await sql_repo.add(original)
    loaded = await sql_repo.get(original.id)

    assert loaded == original, "a stored assessment must come back unchanged"


async def test_sql_find_cached(sql_repo):
    await sql_repo.add(await _make_assessment())

    assert (await sql_repo.find_cached("key-1")) is not None
    assert (await sql_repo.find_cached("no-such-key")) is None


async def test_sql_list_is_newest_first(sql_repo):
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    await sql_repo.add(
        await _make_assessment(
            id="a" * 8 + "-0000-0000-0000-000000000000",
            created_at=now - timedelta(hours=1),
            provider_info={"cache_key": "old"},
        )
    )
    await sql_repo.add(
        await _make_assessment(
            id="b" * 8 + "-0000-0000-0000-000000000000",
            created_at=now,
            provider_info={"cache_key": "new"},
        )
    )

    rows = await sql_repo.list()

    assert [r.provider_info["cache_key"] for r in rows] == ["new", "old"]


# --- blob store ------------------------------------------------------------


async def test_blob_store_deduplicates_by_content(tmp_path):
    store = LocalBlobStore(tmp_path)

    first = await store.put(b"same bytes", "image/png")
    second = await store.put(b"same bytes", "image/png")

    assert first == second == digest_of(b"same bytes")
    assert await store.get(first) == b"same bytes"
    assert len(list(tmp_path.rglob("*"))) < 6, "one blob, not two copies"


async def test_blob_store_returns_none_for_unknown_digest(tmp_path):
    assert await LocalBlobStore(tmp_path).get("f" * 64) is None


async def test_stored_timestamps_stay_timezone_aware(sql_repo):
    """SQLite has no native timestamp type and drops the offset.

    Without the UtcDateTime column type the round-trip returns a naive
    datetime, which then serialises without a 'Z' and breaks any client doing
    date arithmetic against UTC.
    """
    from datetime import UTC

    original = await _make_assessment()
    await sql_repo.add(original)

    loaded = await sql_repo.get(original.id)

    assert loaded is not None
    assert loaded.created_at.tzinfo is not None
    assert loaded.created_at.utcoffset() == UTC.utcoffset(None)
    assert loaded.created_at == original.created_at
