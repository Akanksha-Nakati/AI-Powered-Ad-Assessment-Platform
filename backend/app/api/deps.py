"""FastAPI dependencies.

The container is built once in the lifespan and stashed on ``app.state``; these
pull collaborators off it so route handlers never construct anything.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from backend.app.container import Container
from backend.app.services.assessment_service import AssessmentService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_assessment_service(
    container: Annotated[Container, Depends(get_container)],
) -> AssessmentService:
    return container.assessments


ContainerDep = Annotated[Container, Depends(get_container)]
AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]
