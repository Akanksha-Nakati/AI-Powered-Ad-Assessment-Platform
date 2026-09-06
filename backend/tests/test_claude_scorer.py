"""Claude scorer adapter tests.

The happy path is guaranteed by the API's structured output, so these cover the
failure modes that structured output does *not* cover: refusals, empty parses,
partial scorecards, and transport errors. Each of these used to be a silent
empty scorecard.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.domain.criteria import Criterion
from backend.app.domain.errors import InvalidProviderOutput, ProviderError
from backend.app.domain.models import AdMetadata, AdScorecard
from backend.app.infra.llm.claude_scorer import ClaudeScorer
from backend.tests.fakes import SAMPLE_ANALYSIS, SAMPLE_CHUNKS, _full_scorecard

METADATA = AdMetadata(platform="LinkedIn", industry="SaaS", ad_type="Banner")


class _StubMessages:
    def __init__(self, response=None, error: Exception | None = None):
        self._response = response
        self._error = error
        self.kwargs: dict = {}

    async def parse(self, **kwargs):
        self.kwargs = kwargs
        if self._error:
            raise self._error
        return self._response


def _scorer_with(
    response=None, error: Exception | None = None
) -> tuple[ClaudeScorer, _StubMessages]:
    messages = _StubMessages(response, error)
    scorer = ClaudeScorer(api_key="test", model="claude-opus-5")
    scorer._client = SimpleNamespace(messages=messages)
    return scorer, messages


async def _score(scorer: ClaudeScorer) -> AdScorecard:
    return await scorer.score(SAMPLE_ANALYSIS, SAMPLE_CHUNKS, METADATA)


async def test_returns_parsed_scorecard():
    expected = _full_scorecard()
    scorer, messages = _scorer_with(
        SimpleNamespace(stop_reason="end_turn", parsed_output=expected)
    )

    result = await _score(scorer)

    assert result == expected
    # The schema must be handed to the API, not just described in the prompt.
    assert messages.kwargs["output_format"] is AdScorecard
    assert messages.kwargs["model"] == "claude-opus-5"


async def test_refusal_is_invalid_output_not_a_zero_score():
    scorer, _ = _scorer_with(
        SimpleNamespace(stop_reason="refusal", parsed_output=None)
    )

    with pytest.raises(InvalidProviderOutput):
        await _score(scorer)


async def test_empty_parse_is_invalid_output():
    scorer, _ = _scorer_with(
        SimpleNamespace(stop_reason="end_turn", parsed_output=None)
    )

    with pytest.raises(InvalidProviderOutput):
        await _score(scorer)


async def test_partial_scorecard_is_rejected():
    """Five of six criteria would otherwise average into a plausible overall."""
    partial = _full_scorecard(scores={Criterion.ATTENTION: 8.0})
    scorer, _ = _scorer_with(
        SimpleNamespace(stop_reason="end_turn", parsed_output=partial)
    )

    with pytest.raises(InvalidProviderOutput) as excinfo:
        await _score(scorer)

    assert "clarity" in str(excinfo.value)


async def test_api_error_becomes_provider_error_without_leaking_detail():
    import httpx2
    from anthropic import APIStatusError

    # A real Response, because APIStatusError reaches through to .request.
    response = httpx2.Response(
        401,
        request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"),
    )
    error = APIStatusError(
        "key sk-secret-abc is invalid", response=response, body=None
    )
    scorer, _ = _scorer_with(error=error)

    with pytest.raises(ProviderError) as excinfo:
        await _score(scorer)

    assert "sk-secret-abc" not in str(excinfo.value)
    assert "401" in str(excinfo.value)
