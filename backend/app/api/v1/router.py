from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import assessments, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(assessments.router)
