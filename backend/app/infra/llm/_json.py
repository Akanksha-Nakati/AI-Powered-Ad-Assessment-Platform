"""Shared helper for coaxing JSON out of a text completion.

This exists only for Phase 1, where the Gemini adapters still use the legacy
``google-generativeai`` SDK and cannot enforce a response schema. It is a
narrower, louder version of what the old code did: it still tolerates a model
that wraps JSON in a code fence, but a genuinely unparseable or schema-invalid
reply raises InvalidProviderOutput instead of degrading into an empty result.

Phase 2 replaces the callers with provider-native structured output and this
module goes away.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from backend.app.domain.errors import InvalidProviderOutput

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def parse_model(raw: str | None, schema: type[T], *, provider: str) -> T:
    if not raw or not raw.strip():
        raise InvalidProviderOutput(f"{provider} returned an empty response")

    candidate = raw.strip()
    fenced = _FENCE.match(candidate)
    if fenced:
        candidate = fenced.group(1)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidProviderOutput(
            f"{provider} did not return valid JSON: {exc.msg}"
        ) from exc

    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise InvalidProviderOutput(
            f"{provider} returned JSON that is not a valid {schema.__name__}: "
            f"{exc.error_count()} validation error(s)"
        ) from exc
