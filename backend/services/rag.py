import json
from pathlib import Path
from typing import List

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.config import settings
from backend.services.doc_generator import ensure_marketing_docs


def _build_vectorstore(docs_path: Path, persist_path: Path) -> Chroma:
    ensure_marketing_docs(docs_path)

    texts: List[Document] = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    for path in docs_path.glob("*.md"):
        raw = path.read_text(encoding="utf-8")
        chunks = splitter.split_text(raw)
        for i, chunk in enumerate(chunks):
            metadata = {"source": path.name, "chunk": i}
            texts.append(Document(page_content=chunk, metadata=metadata))

    embeddings = GoogleGenerativeAIEmbeddings(
        google_api_key=settings.google_api_key,
        model=settings.gemini_embedding_model,
    )
    vectordb = Chroma.from_documents(
        texts,
        embedding=embeddings,
        persist_directory=str(persist_path),
    )
    vectordb.persist()
    return vectordb


def load_vectorstore() -> Chroma:
    persist_path = settings.chroma_path
    docs_path = settings.docs_path
    persist_path.mkdir(parents=True, exist_ok=True)
    docs_path.mkdir(parents=True, exist_ok=True)

    # Reuse existing store if present
    if any(persist_path.glob("**/*")):
        embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=settings.google_api_key,
            model=settings.gemini_embedding_model,
        )
        return Chroma(
            embedding_function=embeddings,
            persist_directory=str(persist_path),
        )
    return _build_vectorstore(docs_path, persist_path)


def retrieve_context(query: str, k: int = None) -> List[Document]:
    store = load_vectorstore()
    retriever = store.as_retriever(
        search_kwargs={"k": k or settings.retrieval_k}
    )
    return retriever.get_relevant_documents(query)


def serialize_docs(docs: List[Document]) -> List[dict]:
    serialized = []
    for doc in docs:
        serialized.append(
            {
                "text": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "chunk": doc.metadata.get("chunk"),
            }
        )
    return serialized

