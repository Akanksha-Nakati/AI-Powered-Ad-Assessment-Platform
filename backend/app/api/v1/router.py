from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import assessments, brands, comparisons, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(assessments.router)
api_router.include_router(brands.router)
api_router.include_router(comparisons.router)
