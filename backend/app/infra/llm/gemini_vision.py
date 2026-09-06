"""Gemini vision adapter -- implements the VisionAnalyzer port.

Uses the current google-genai SDK: a native async client (no thread offloading)
and ``response_schema``, so the model's reply is schema-constrained rather than
prompted-for and hopefully-parseable.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.domain.errors import InvalidProviderOutput, ProviderError
from backend.app.domain.models import VisualAnalysis

logger = logging.getLogger(__name__)

PROMPT = (
    "You are a marketing creative analyst. Describe this ad image: its dominant "
    "colors, the key copy you can read, the composition and focal areas, the "
    "visible call-to-action text (empty string if there is none), and up to "
    "three short observations about its strengths and risks."
)


class GeminiVisionAnalyzer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def analyze(self, image: bytes, media_type: str) -> VisualAnalysis:
        from google.genai import errors as genai_errors
        from google.genai import types

        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=image, mime_type=media_type),
                    PROMPT,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VisualAnalysis,
                ),
            )
        except genai_errors.APIError as exc:
            logger.warning("gemini vision failed: %s", type(exc).__name__)
            raise ProviderError(
                f"gemini vision request failed: {type(exc).__name__}"
            ) from exc

        parsed = response.parsed
        if parsed is None:
            raise InvalidProviderOutput("gemini vision returned no parsed analysis")
        if isinstance(parsed, VisualAnalysis):
            return parsed
        # The SDK hands back a dict when it cannot instantiate the schema class.
        return VisualAnalysis.model_validate(parsed)
