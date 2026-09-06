from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from backend.app.api.deps import AssessmentServiceDep
from backend.app.domain.errors import NotFoundError
from backend.app.domain.models import AdMetadata, Assessment

router = APIRouter(prefix="/assessments", tags=["assessments"])

#: Guards against a large upload becoming a large, slow, expensive model call.
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


@router.post("", response_model=Assessment, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    service: AssessmentServiceDep,
    ad_image: UploadFile = File(...),
    platform: str = Form(...),
    industry: str = Form(...),
    ad_type: str = Form(...),
    brand_id: str | None = Form(None),
) -> Assessment:
    media_type = (ad_image.content_type or "").lower()
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type. Expected one of: "
            f"{', '.join(sorted(ALLOWED_MEDIA_TYPES))}.",
        )

    image = await ad_image.read()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty."
        )
    if len(image) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {MAX_IMAGE_BYTES // (1024 * 1024)}MB.",
        )

    # Domain errors raised below are translated by the handler in api/errors.py.
    return await service.assess(
        image=image,
        media_type=media_type,
        metadata=AdMetadata(platform=platform, industry=industry, ad_type=ad_type),
        brand_id=brand_id,
    )


@router.get("", response_model=list[Assessment])
async def list_assessments(
    service: AssessmentServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Assessment]:
    """Assessment history, most recent first."""
    return await service.history(limit=limit, offset=offset)


@router.get("/{assessment_id}", response_model=Assessment)
async def get_assessment(
    assessment_id: str,
    service: AssessmentServiceDep,
) -> Assessment:
    assessment = await service.get(assessment_id)
    if assessment is None:
        raise NotFoundError(f"no assessment with id {assessment_id}")
    return assessment
