"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.errors import register_error_handlers
from backend.app.api.v1.router import api_router
from backend.app.config import Settings
from backend.app.config import settings as default_settings
from backend.app.container import Container, build_container

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app.

    Takes settings as an argument so tests can construct an app with fakes
    instead of mutating module-level state.
    """
    resolved = settings or default_settings

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container: Container = build_container(resolved)
        app.state.container = container
        try:
            # Warming the store here is what stops every request paying to
            # re-open the collection, as the previous implementation did.
            await container.knowledge.ensure_ready()
        except Exception:
            logger.exception(
                "knowledge store failed to initialise; /health will report not ready"
            )
        yield

    app = FastAPI(
        title="Ad Assessment API",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
