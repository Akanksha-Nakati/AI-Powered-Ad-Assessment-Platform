"""Domain error -> HTTP status, in one place.

The previous code wrapped each pipeline stage in ``except Exception`` and put
``str(exc)`` in the response body, which both flattened every failure to 500 and
leaked provider internals to the browser. Here the mapping is explicit and the
client sees a stable, non-revealing message while the detail goes to the log.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.app.domain.errors import (
    ConfigurationError,
    DomainError,
    InvalidProviderOutput,
    KnowledgeStoreUnavailable,
    NotFoundError,
    ProviderError,
)

logger = logging.getLogger(__name__)

#: Most specific first -- the first matching entry wins.
_STATUS_MAP: list[tuple[type[DomainError], int, str]] = [
    (NotFoundError, status.HTTP_404_NOT_FOUND, "Not found."),
    (
        InvalidProviderOutput,
        status.HTTP_502_BAD_GATEWAY,
        "The model returned a response we could not score. Please retry.",
    ),
    (
        ProviderError,
        status.HTTP_502_BAD_GATEWAY,
        "An upstream model provider failed. Please retry.",
    ),
    (
        KnowledgeStoreUnavailable,
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "The marketing knowledge base is not ready yet.",
    ),
    (
        ConfigurationError,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "The server is misconfigured.",
    ),
]


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        for error_type, http_status, message in _STATUS_MAP:
            if isinstance(exc, error_type):
                logger.warning("%s: %s", type(exc).__name__, exc, exc_info=exc)
                return JSONResponse(
                    status_code=http_status,
                    content={"detail": message, "error": type(exc).__name__},
                )

        logger.exception("unhandled domain error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Unexpected error.", "error": type(exc).__name__},
        )
