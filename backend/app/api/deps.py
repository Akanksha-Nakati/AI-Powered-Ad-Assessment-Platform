"""FastAPI dependencies.

The container is built once in the lifespan and stashed on ``app.state``; these
pull collaborators off it so route handlers never construct anything.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from backend.app.container import Container
from backend.app.services.assessment_service import AssessmentService
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.services.performance_service import PerformanceService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_assessment_service(
    container: Annotated[Container, Depends(get_container)],
) -> AssessmentService:
    return container.assessments


def get_knowledge_service(
    container: Annotated[Container, Depends(get_container)],
) -> KnowledgeService:
    return container.knowledge_service


def get_comparison_service(
    container: Annotated[Container, Depends(get_container)],
) -> ComparisonService:
    return container.comparisons


def get_performance_service(
    container: Annotated[Container, Depends(get_container)],
) -> PerformanceService:
    return container.performance


ContainerDep = Annotated[Container, Depends(get_container)]
AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]
KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]
ComparisonServiceDep = Annotated[ComparisonService, Depends(get_comparison_service)]
PerformanceServiceDep = Annotated[
    PerformanceService, Depends(get_performance_service)
]
