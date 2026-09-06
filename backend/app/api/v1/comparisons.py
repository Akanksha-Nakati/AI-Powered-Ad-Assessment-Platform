from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.app.api.deps import ComparisonServiceDep
from backend.app.api.v1.assessments import ALLOWED_MEDIA_TYPES, MAX_IMAGE_BYTES
from backend.app.domain.models import AdMetadata, Comparison

router = APIRouter(prefix="/comparisons", tags=["comparisons"])

MIN_VARIANTS = 2
MAX_VARIANTS = 5


@router.post("", response_model=Comparison, status_code=status.HTTP_201_CREATED)
async def create_comparison(
    service: ComparisonServiceDep,
    ad_images: list[UploadFile] = File(...),
    platform: str = Form(...),
    industry: str = Form(...),
    ad_type: str = Form(...),
    brand_id: str | None = Form(None),
) -> Comparison:
    """Score several variants of the same ad and rank them."""
    if not MIN_VARIANTS <= len(ad_images) <= MAX_VARIANTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Upload between {MIN_VARIANTS} and {MAX_VARIANTS} variants.",
        )

    variants: list[tuple[str, bytes, str]] = []
    for index, upload in enumerate(ad_images):
        media_type = (upload.content_type or "").lower()
        label = upload.filename or f"variant-{index + 1}"

        if media_type not in ALLOWED_MEDIA_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"{label}: unsupported image type {media_type!r}.",
            )
        data = await upload.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"{label} is empty."
            )
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{label} exceeds {MAX_IMAGE_BYTES // (1024 * 1024)}MB.",
            )
        variants.append((label, data, media_type))

    return await service.compare(
        variants,
        AdMetadata(platform=platform, industry=industry, ad_type=ad_type),
        brand_id=brand_id,
    )
