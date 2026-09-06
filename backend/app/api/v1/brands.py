from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from backend.app.api.deps import KnowledgeServiceDep
from backend.app.domain.models import Brand, KnowledgeDocument
from backend.app.services.knowledge_service import MAX_DOCUMENT_BYTES

router = APIRouter(prefix="/brands", tags=["brands"])

ALLOWED_DOC_TYPES = {"text/markdown", "text/plain", "application/octet-stream"}
ALLOWED_DOC_SUFFIXES = (".md", ".txt", ".markdown")


class CreateBrandRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


@router.post("", response_model=Brand, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: CreateBrandRequest, service: KnowledgeServiceDep
) -> Brand:
    return await service.create_brand(payload.name)


@router.get("", response_model=list[Brand])
async def list_brands(service: KnowledgeServiceDep) -> list[Brand]:
    return await service.list_brands()


@router.get("/{brand_id}", response_model=Brand)
async def get_brand(brand_id: str, service: KnowledgeServiceDep) -> Brand:
    return await service.get_brand(brand_id)


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_brand(brand_id: str, service: KnowledgeServiceDep) -> Response:
    await service.delete_brand(brand_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{brand_id}/documents", response_model=list[KnowledgeDocument])
async def list_documents(
    brand_id: str, service: KnowledgeServiceDep
) -> list[KnowledgeDocument]:
    return await service.list_documents(brand_id)


@router.post(
    "/{brand_id}/documents",
    response_model=KnowledgeDocument,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    brand_id: str,
    service: KnowledgeServiceDep,
    document: UploadFile = File(...),
) -> KnowledgeDocument:
    filename = document.filename or "untitled.md"
    if not filename.lower().endswith(ALLOWED_DOC_SUFFIXES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Expected a text document ({', '.join(ALLOWED_DOC_SUFFIXES)}).",
        )

    raw = await document.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The document is empty."
        )
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Document exceeds {MAX_DOCUMENT_BYTES // 1024}KB.",
        )

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The document must be UTF-8 text.",
        ) from None

    return await service.ingest_document(brand_id, filename, content)
