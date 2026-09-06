"""Brand knowledge ingestion.

Turns an uploaded document into embedded, retrievable chunks scoped to one
brand. This is what makes the product's actual claim true -- that it knows
*your* guidelines, not just the three files shipped in the repository.
"""

from __future__ import annotations

import hashlib
import logging

from backend.app.domain.errors import ConflictError, NotFoundError
from backend.app.domain.models import Brand, KnowledgeDocument
from backend.app.domain.ports import BrandRepository, KnowledgeStore

logger = logging.getLogger(__name__)

#: Generous for a brand guidelines document, small enough that one upload
#: cannot produce an unbounded embedding bill.
MAX_DOCUMENT_BYTES = 1024 * 1024


class KnowledgeService:
    def __init__(self, brands: BrandRepository, store: KnowledgeStore) -> None:
        self._brands = brands
        self._store = store

    async def create_brand(self, name: str) -> Brand:
        name = name.strip()
        if not name:
            raise ConflictError("brand name cannot be empty")
        return await self._brands.create(name)

    async def list_brands(self) -> list[Brand]:
        return await self._brands.list_brands()

    async def get_brand(self, brand_id: str) -> Brand:
        brand = await self._brands.get(brand_id)
        if brand is None:
            raise NotFoundError(f"no brand with id {brand_id}")
        return brand

    async def delete_brand(self, brand_id: str) -> None:
        if not await self._brands.delete(brand_id):
            raise NotFoundError(f"no brand with id {brand_id}")
        # Vectors outlive the row unless they are explicitly dropped, and an
        # orphaned chunk would keep being cited for a brand that no longer
        # exists.
        await self._store.remove_brand(brand_id)

    async def list_documents(self, brand_id: str) -> list[KnowledgeDocument]:
        await self.get_brand(brand_id)
        return await self._brands.list_documents(brand_id)

    async def ingest_document(
        self, brand_id: str, filename: str, content: str
    ) -> KnowledgeDocument:
        await self.get_brand(brand_id)

        content_sha256 = hashlib.sha256(content.encode()).hexdigest()
        existing = await self._brands.find_document_by_hash(brand_id, content_sha256)
        if existing is not None and existing.filename == filename:
            # Identical bytes under the same name: re-embedding would cost money
            # and change nothing.
            logger.info("skipping unchanged document %s for brand %s", filename, brand_id)
            return existing

        chunk_count = await self._store.ingest_brand_document(
            brand_id, filename, content
        )
        return await self._brands.add_document(
            brand_id=brand_id,
            filename=filename,
            content=content,
            content_sha256=content_sha256,
            chunk_count=chunk_count,
        )
