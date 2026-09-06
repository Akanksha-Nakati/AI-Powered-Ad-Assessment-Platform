"""Composition root.

The only module that decides which concrete adapter satisfies which port.
Everything else receives its collaborators. Swapping Gemini for Claude, or a
real store for a fake, is a change here and nowhere else.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.config import Settings
from backend.app.domain.errors import ConfigurationError
from backend.app.domain.ports import (
    AssessmentRepository,
    BlobStore,
    BrandRepository,
    KnowledgeStore,
    Scorer,
    VisionAnalyzer,
)
from backend.app.services.assessment_service import AssessmentService
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.knowledge_service import KnowledgeService


@dataclass(slots=True)
class Container:
    settings: Settings
    vision: VisionAnalyzer
    scorer: Scorer
    knowledge: KnowledgeStore
    repository: AssessmentRepository
    brands: BrandRepository
    blobs: BlobStore
    assessments: AssessmentService
    comparisons: ComparisonService
    knowledge_service: KnowledgeService
    engine: object | None = None


def build_container(settings: Settings) -> Container:
    missing = settings.missing_keys()
    if missing:
        # Fail at startup with the list, rather than on the first request with
        # whichever key happened to be checked first.
        raise ConfigurationError(
            "missing required credentials: " + ", ".join(missing)
        )

    vision = _build_vision(settings)
    scorer = _build_scorer(settings)
    knowledge = _build_knowledge(settings)
    engine, repository, brands = _build_repositories(settings)
    blobs = _build_blobs(settings)

    service = AssessmentService(
        vision=vision,
        scorer=scorer,
        knowledge=knowledge,
        repository=repository,
        blobs=blobs,
        retrieval_k=settings.retrieval_k,
        prompt_version=settings.prompt_version,
        provider_info={
            "vision_provider": settings.vision_provider,
            "scoring_provider": settings.scoring_provider,
            "scoring_model": _scoring_model(settings),
        },
    )
    return Container(
        settings=settings,
        vision=vision,
        scorer=scorer,
        knowledge=knowledge,
        repository=repository,
        brands=brands,
        blobs=blobs,
        assessments=service,
        comparisons=ComparisonService(
            service, max_concurrency=settings.comparison_concurrency
        ),
        knowledge_service=KnowledgeService(brands, knowledge),
        engine=engine,
    )


def _scoring_model(settings: Settings) -> str:
    return (
        settings.claude_model
        if settings.scoring_provider == "claude"
        else settings.gemini_model
    )


def _build_vision(settings: Settings) -> VisionAnalyzer:
    if settings.vision_provider == "gemini":
        from backend.app.infra.llm.gemini_vision import GeminiVisionAnalyzer

        return GeminiVisionAnalyzer(
            api_key=settings.google_api_key, model=settings.gemini_model
        )
    raise ConfigurationError(f"unknown vision provider: {settings.vision_provider}")


def _build_scorer(settings: Settings) -> Scorer:
    if settings.scoring_provider == "gemini":
        from backend.app.infra.llm.gemini_scorer import GeminiScorer

        return GeminiScorer(
            api_key=settings.google_api_key, model=settings.gemini_model
        )
    if settings.scoring_provider == "claude":
        from backend.app.infra.llm.claude_scorer import ClaudeScorer

        return ClaudeScorer(
            api_key=settings.anthropic_api_key, model=settings.claude_model
        )
    raise ConfigurationError(f"unknown scoring provider: {settings.scoring_provider}")


def _build_knowledge(settings: Settings) -> KnowledgeStore:
    from backend.app.infra.rag.chroma_store import ChromaKnowledgeStore

    return ChromaKnowledgeStore(
        docs_path=settings.docs_path,
        persist_path=settings.chroma_path,
        embedding_model=settings.gemini_embedding_model,
        google_api_key=settings.google_api_key,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        retrieval_k=settings.retrieval_k,
    )


def _build_repositories(
    settings: Settings,
) -> tuple[object, AssessmentRepository, BrandRepository]:
    from backend.app.infra.db.repositories import (
        SqlAssessmentRepository,
        SqlBrandRepository,
    )
    from backend.app.infra.db.session import create_engine, create_session_factory

    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    return engine, SqlAssessmentRepository(factory), SqlBrandRepository(factory)


def _build_blobs(settings: Settings) -> BlobStore:
    from backend.app.infra.storage.local_blob import LocalBlobStore

    settings.blob_path.mkdir(parents=True, exist_ok=True)
    return LocalBlobStore(settings.blob_path)
