import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    gemini_embedding_model: str = "models/text-embedding-004"
    gemini_model: str = "gemini-1.5-flash"
    gemini_text_model: str = "gemini-1.5-flash"
    chroma_path: Path = Path(__file__).resolve().parent / "storage" / "chroma"
    docs_path: Path = Path(__file__).resolve().parent / "data" / "marketing_docs"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4
    claude_model: str = "claude-3-5-sonnet-20240620"
    gemini_model: str = "gemini-1.5-flash"
    frontend_origin: Optional[str] = os.getenv("FRONTEND_ORIGIN")

    class Config:
        env_file = ".env"
        env_prefix = "APP_"


settings = Settings()

