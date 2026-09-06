"""Chroma-backed knowledge store.

Fixes three defects in the previous backend/services/rag.py:

* ``retrieve_context`` called ``load_vectorstore()`` on *every request*, so each
  assessment paid to re-open the collection. The store is built once in
  ``ensure_ready`` and held.
* Once the persist directory was non-empty it was never rebuilt, so edits to the
  marketing docs never took effect. The corpus is content-hashed now.
* Nothing recorded which embedding model produced the vectors. Switching models
  silently invalidates every vector -- similarity against a differently-embedded
  index is meaningless rather than merely wrong. The hash covers the model name,
  so a model change forces a rebuild instead of quietly degrading retrieval.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from backend.app.domain.errors import KnowledgeStoreUnavailable
from backend.app.domain.models import RetrievedChunk
from backend.app.infra.rag.seed_docs import ensure_marketing_docs

logger = logging.getLogger(__name__)

#: Written next to the vectors so a later process can tell what produced them.
MANIFEST_NAME = "index_manifest.json"


def corpus_fingerprint(docs_path: Path, embedding_model: str, chunk_size: int,
                       chunk_overlap: int) -> str:
    """Hash everything that, if changed, invalidates the persisted vectors."""
    h = hashlib.sha256()
    h.update(embedding_model.encode())
    h.update(f"{chunk_size}:{chunk_overlap}".encode())
    for path in sorted(docs_path.glob("*.md")):
        h.update(path.name.encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


class ChromaKnowledgeStore:
    """Implements the KnowledgeStore port."""

    def __init__(
        self,
        *,
        docs_path: Path,
        persist_path: Path,
        embedding_model: str,
        google_api_key: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        retrieval_k: int = 4,
    ) -> None:
        self._docs_path = docs_path
        self._persist_path = persist_path
        self._embedding_model = embedding_model
        self._google_api_key = google_api_key
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._retrieval_k = retrieval_k
        self._store: Any = None
        self._lock = asyncio.Lock()

    # --- lifecycle -------------------------------------------------------

    async def ensure_ready(self) -> None:
        async with self._lock:
            if self._store is not None:
                return
            try:
                self._store = await asyncio.to_thread(self._build_or_open)
            except Exception as exc:
                raise KnowledgeStoreUnavailable(
                    "could not initialise the vector store"
                ) from exc

    def _manifest_path(self) -> Path:
        return self._persist_path / MANIFEST_NAME

    def _is_current(self, fingerprint: str) -> bool:
        manifest = self._manifest_path()
        if not manifest.exists():
            return False
        try:
            recorded = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            return False
        return recorded.get("fingerprint") == fingerprint

    def _build_or_open(self) -> Any:
        # Imported lazily so the domain and service layers stay importable
        # without LangChain installed. langchain-chroma replaces the deprecated
        # langchain_community.vectorstores.Chroma.
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        self._docs_path.mkdir(parents=True, exist_ok=True)
        self._persist_path.mkdir(parents=True, exist_ok=True)
        ensure_marketing_docs(self._docs_path)

        fingerprint = corpus_fingerprint(
            self._docs_path, self._embedding_model, self._chunk_size, self._chunk_overlap
        )
        embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=self._google_api_key, model=self._embedding_model
        )

        has_vectors = any(self._persist_path.glob("*.sqlite3"))
        if has_vectors and self._is_current(fingerprint):
            logger.info(
                "opening existing vector store (fingerprint %s)", fingerprint[:12]
            )
            return Chroma(
                embedding_function=embeddings,
                persist_directory=str(self._persist_path),
            )

        logger.info("building vector store (fingerprint %s)", fingerprint[:12])
        store = Chroma.from_documents(
            self._split_documents(),
            embedding=embeddings,
            persist_directory=str(self._persist_path),
        )
        self._manifest_path().write_text(
            json.dumps(
                {
                    "fingerprint": fingerprint,
                    "embedding_model": self._embedding_model,
                    "chunk_size": self._chunk_size,
                    "chunk_overlap": self._chunk_overlap,
                },
                indent=2,
            )
        )
        return store

    def _split_documents(self) -> list[Any]:
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap
        )
        documents: list = []
        for path in sorted(self._docs_path.glob("*.md")):
            for index, chunk in enumerate(splitter.split_text(path.read_text("utf-8"))):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={"source": path.name, "chunk": index, "scope": "global"},
                    )
                )
        if not documents:
            raise KnowledgeStoreUnavailable("no marketing documents to index")
        return documents

    # --- retrieval -------------------------------------------------------

    async def retrieve(
        self,
        query: str,
        k: int | None = None,
        brand_id: str | None = None,
    ) -> list[RetrievedChunk]:
        if self._store is None:
            raise KnowledgeStoreUnavailable("vector store has not been initialised")

        limit = k or self._retrieval_k
        try:
            documents = await asyncio.to_thread(
                self._store.similarity_search, query, limit
            )
        except Exception as exc:
            raise KnowledgeStoreUnavailable("retrieval failed") from exc

        return [
            RetrievedChunk(
                text=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                chunk=doc.metadata.get("chunk"),
                brand_id=doc.metadata.get("brand_id"),
            )
            for doc in documents
        ]
