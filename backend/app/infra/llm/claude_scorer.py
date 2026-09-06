"""Claude scoring adapter -- implements the Scorer port.

This is the judgement step the README always advertised and the code never did.
It uses provider-native structured output: ``messages.parse(output_format=...)``
returns an ``AdScorecard`` the API has already validated against the schema, so
there is no JSON string to parse and no parse failure to swallow.
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
from backend.app.infra.llm.prompts import SYSTEM_INSTRUCTION, build_scoring_prompt

logger = logging.getLogger(__name__)

#: Scoring output is small (six numbers, a paragraph, five bullets). This is
#: generous for it while staying well under the non-streaming timeout.
MAX_TOKENS = 4096


class ClaudeScorer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def score(
        self,
        analysis: VisualAnalysis,
        context: list[RetrievedChunk],
        metadata: AdMetadata,
    ) -> AdScorecard:
        from anthropic import APIError, APIStatusError

        client = self._get_client()
        prompt = build_scoring_prompt(analysis, context, metadata)

        try:
            response = await client.messages.parse(
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_INSTRUCTION,
                messages=[{"role": "user", "content": prompt}],
                output_format=AdScorecard,
            )
        except APIStatusError as exc:
            # Deliberately does not include the provider body -- it can contain
            # request echoes. The detail goes to the log, not the client.
            logger.warning(
                "claude scoring failed: status=%s: %s", exc.status_code, exc
            )
            raise ProviderError(
                f"claude scoring request failed with status {exc.status_code}"
            ) from exc
        except APIError as exc:
            logger.warning("claude scoring failed: %s", type(exc).__name__)
            raise ProviderError(
                f"claude scoring request failed: {type(exc).__name__}"
            ) from exc

        # A safety refusal returns HTTP 200 with no usable content, so it has to
        # be checked explicitly rather than caught.
        if response.stop_reason == "refusal":
            raise InvalidProviderOutput("claude declined to score this creative")

        scorecard = response.parsed_output
        if scorecard is None:
            raise InvalidProviderOutput("claude returned no parsed scorecard")

        _reject_partial(scorecard)
        return scorecard


def _reject_partial(scorecard: AdScorecard) -> None:
    """All six criteria or nothing.

    Structured output guarantees the shape, not that the model filled in every
    key with something meaningful; a missing criterion would otherwise skew the
    derived overall score.
    """
    missing = [c.value for c in Criterion if c not in scorecard.scores]
    if missing:
        raise InvalidProviderOutput(
            f"claude omitted required criteria: {', '.join(missing)}"
        )
