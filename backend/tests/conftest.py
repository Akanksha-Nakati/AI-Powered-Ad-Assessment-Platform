from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.errors import register_error_handlers
from backend.app.api.v1.router import api_router
from backend.app.config import Settings
from backend.app.container import Container
from backend.app.services.assessment_service import AssessmentService
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.services.performance_service import PerformanceService
from backend.tests.fakes import (
    FakeAssessmentRepository,
    FakeBlobStore,
    FakeBrandRepository,
    FakeDataSourceRepository,
    FakeKnowledgeStore,
    FakePerformanceSource,
    FakeScorer,
    FakeVisionAnalyzer,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(google_api_key="test-key", anthropic_api_key="test-key")


def build_test_app(container: Container) -> FastAPI:
    """An app wired to whatever container the test supplies.

    Deliberately does not use the production lifespan: the point is that no
    adapter, credential or network call is involved.
    """
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    app.state.container = container
    return app


@pytest.fixture
def make_client(settings):
    def _make(
        vision: FakeVisionAnalyzer | None = None,
        scorer: FakeScorer | None = None,
        knowledge: FakeKnowledgeStore | None = None,
        repository: FakeAssessmentRepository | None = None,
        blobs: FakeBlobStore | None = None,
        brands: FakeBrandRepository | None = None,
        data_sources: FakeDataSourceRepository | None = None,
        warehouse: FakePerformanceSource | None = None,
    ) -> tuple[TestClient, Container]:
        vision = vision or FakeVisionAnalyzer()
        scorer = scorer or FakeScorer()
        knowledge = knowledge or FakeKnowledgeStore()
        repository = repository if repository is not None else FakeAssessmentRepository()
        blobs = blobs if blobs is not None else FakeBlobStore()
        brands = brands if brands is not None else FakeBrandRepository()
        data_sources = (
            data_sources if data_sources is not None else FakeDataSourceRepository()
        )
        warehouse = warehouse if warehouse is not None else FakePerformanceSource()
        assessment_service = AssessmentService(
            vision=vision,
            scorer=scorer,
            knowledge=knowledge,
            repository=repository,
            blobs=blobs,
            retrieval_k=settings.retrieval_k,
            prompt_version=settings.prompt_version,
            provider_info={"scoring_model": "fake"},
        )
        container = Container(
            settings=settings,
            vision=vision,
            scorer=scorer,
            knowledge=knowledge,
            repository=repository,
            brands=brands,
            blobs=blobs,
            knowledge_service=KnowledgeService(brands, knowledge),
            comparisons=ComparisonService(assessment_service),
            assessments=assessment_service,
            data_sources=data_sources,
            warehouse=warehouse,
            performance=PerformanceService(data_sources, warehouse, repository),
        )
        return TestClient(build_test_app(container)), container

    return _make


@pytest.fixture
def png_bytes() -> bytes:
    """Smallest valid PNG, so uploads are real bytes without a fixture file."""
    import base64

    return base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
