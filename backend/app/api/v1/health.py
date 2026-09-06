from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.api.deps import ContainerDep

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    knowledge_ready: bool
    vision_provider: str
    scoring_provider: str


@router.get("/health", response_model=HealthResponse)
async def health(container: ContainerDep) -> HealthResponse:
    settings = container.settings
    return HealthResponse(
        status="ok",
        knowledge_ready=getattr(container.knowledge, "is_ready", False),
        vision_provider=settings.vision_provider,
        scoring_provider=settings.scoring_provider,
    )
