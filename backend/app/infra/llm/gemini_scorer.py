"""Gemini scoring adapter -- implements the Scorer port."""

from __future__ import annotations

import asyncio

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import InvalidProviderOutput, ProviderError
from backend.app.domain.models import (
    AdMetadata,
    AdScorecard,
    RetrievedChunk,
    VisualAnalysis,
)
from backend.app.infra.llm._json import parse_model
from backend.app.infra.llm.prompts import build_scoring_prompt


class GeminiScorer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def score(
        self,
        analysis: VisualAnalysis,
        context: list[RetrievedChunk],
        metadata: AdMetadata,
    ) -> AdScorecard:
        prompt = build_scoring_prompt(analysis, context, metadata)
        raw = await asyncio.to_thread(self._generate, prompt)
        scorecard = parse_model(raw, AdScorecard, provider="gemini-scorer")
        _reject_partial(scorecard, provider="gemini-scorer")
        return scorecard

    def _generate(self, prompt: str) -> str | None:
        import google.generativeai as genai

        try:
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model)
            return model.generate_content(prompt).text
        except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
            raise ProviderError(
                f"gemini scoring request failed: {type(exc).__name__}"
            ) from exc


def _reject_partial(scorecard: AdScorecard, *, provider: str) -> None:
    """A scorecard missing criteria is a failure, not a low score.

    The old code averaged whatever subset came back, so a provider that scored
    two of six criteria produced a confident-looking overall figure.
    """
    missing = [c.value for c in Criterion if c not in scorecard.scores]
    if missing:
        raise InvalidProviderOutput(
            f"{provider} omitted required criteria: {', '.join(missing)}"
        )
