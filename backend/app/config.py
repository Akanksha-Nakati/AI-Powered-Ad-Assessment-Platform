"""Application settings -- one source of truth.

Two bugs from the previous config are fixed here:

* ``env_prefix = "APP_"`` meant pydantic-settings looked for ``APP_GOOGLE_API_KEY``.
  The plain ``GOOGLE_API_KEY`` was only picked up because the field also had an
  ``os.getenv`` default factory, so the setting worked by accident and any new
  field would silently fail to load. The prefix is gone.
* ``gemini_model`` was declared twice and a ``claude_model`` was declared but
  never used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

VisionProvider = Literal["gemini"]
ScoringProvider = Literal["gemini", "claude"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Credentials ---
    google_api_key: str = ""
    anthropic_api_key: str = ""
    #: Encrypts data-source connection secrets at rest. Only required to
    #: create a data source, not at startup -- most deployments won't touch
    #: this feature immediately. Generate with:
    #: python -c "from cryptography.fernet import Fernet; \
    #: print(Fernet.generate_key().decode())"
    warehouse_encryption_key: str = ""

    # --- Provider selection (resolved in app/container.py) ---
    vision_provider: VisionProvider = "gemini"
    scoring_provider: ScoringProvider = "claude"

    # --- Models ---
    # Provider model IDs get retired fast. Both values the project originally
    # shipped with (gemini-1.5-flash, models/text-embedding-004) now 404, and so
    # does gemini-2.5-flash for new keys. `python -m backend.app.cli models`
    # lists what the configured key can reach -- note that a model appearing
    # there is not proof it is callable, since some are listed but closed to new
    # users; the 404 body names the replacement.
    gemini_model: str = "gemini-3.6-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    claude_model: str = "claude-opus-5"

    # --- Persistence ---
    #: Swap for postgresql+asyncpg://... to move off SQLite; no code changes.
    database_url: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'storage' / 'app.db'}"
    blob_path: Path = BACKEND_DIR / "storage" / "blobs"

    # --- Retrieval ---
    chroma_path: Path = BACKEND_DIR / "storage" / "chroma"
    docs_path: Path = BACKEND_DIR / "data" / "marketing_docs"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4

    # --- Comparison ---
    #: Bounds concurrent provider calls when several variants are compared.
    comparison_concurrency: int = 4

    # --- Data warehouse connections ---
    #: A hung or slow user-supplied query is stopped from this side; the
    #: underlying blocking DBAPI call may keep running past it regardless.
    warehouse_query_timeout_seconds: int = 30

    # --- Prompting ---
    #: Bumped whenever a prompt changes; part of the assessment cache key so a
    #: prompt edit invalidates cached scorecards instead of serving stale ones.
    prompt_version: str = "v1"

    # --- HTTP ---
    frontend_origin: str | None = None

    def cors_origins(self) -> list[str]:
        """Explicit dev origins by default.

        The previous config sent ``allow_origins=["*"]`` together with
        ``allow_credentials=True``, a combination browsers reject outright.
        """
        if self.frontend_origin:
            return [self.frontend_origin]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    def required_keys_for(
        self, vision: VisionProvider, scoring: ScoringProvider
    ) -> list[str]:
        """Which credentials the chosen providers actually need."""
        needed: set[str] = set()
        if vision == "gemini" or scoring == "gemini":
            needed.add("GOOGLE_API_KEY")
        if scoring == "claude":
            needed.add("ANTHROPIC_API_KEY")
        # Embeddings are Gemini-backed regardless of the chat providers.
        needed.add("GOOGLE_API_KEY")
        return sorted(needed)

    def missing_keys(self) -> list[str]:
        values = {
            "GOOGLE_API_KEY": self.google_api_key,
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
        }
        return [
            key
            for key in self.required_keys_for(self.vision_provider, self.scoring_provider)
            if not values.get(key)
        ]


settings = Settings()
