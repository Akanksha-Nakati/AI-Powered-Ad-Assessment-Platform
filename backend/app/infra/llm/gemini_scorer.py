"""Gemini scoring adapter -- implements the Scorer port.

Kept as the second implementation of Scorer so the port is demonstrably not
shaped around one vendor, and so scoring still works with only a GOOGLE_API_KEY.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import InvalidProviderOutput, ProviderError
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    RetrievedChunk,
    VisualAnalysis,
)
from backend.app.infra.llm.gemini_client import build_client
from backend.app.infra.llm.gemini_schemas import GeminiScorecard
from backend.app.infra.llm.prompts import SYSTEM_INSTRUCTION, build_scoring_prompt

logger = logging.getLogger(__name__)


class GeminiScorer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = build_client(self._api_key)
        return self._client

    async def score(
        self,
        analysis: VisualAnalysis,
        context: list[RetrievedChunk],
        metadata: AdMetadata,
    ) -> AdScorecard:
        from google.genai import errors as genai_errors
        from google.genai import types

        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=build_scoring_prompt(analysis, context, metadata),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=GeminiScorecard,
                ),
            )
        except genai_errors.APIError as exc:
            logger.warning("gemini scoring failed: %s: %s", type(exc).__name__, exc)
            raise ProviderError(
                f"gemini scoring request failed: {type(exc).__name__}"
            ) from exc

        parsed = response.parsed
        if parsed is None:
            raise InvalidProviderOutput("gemini returned no parsed scorecard")
        if not isinstance(parsed, GeminiScorecard):
            parsed = GeminiScorecard.model_validate(parsed)
        scorecard = parsed.to_domain()

        missing = [c.value for c in Criterion if c not in scorecard.scores]
        if missing:
            raise InvalidProviderOutput(
                f"gemini omitted required criteria: {', '.join(missing)}"
            )
        return scorecard
