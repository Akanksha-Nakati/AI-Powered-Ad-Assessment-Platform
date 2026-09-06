"""Shared Gemini client construction.

Retries are configured here rather than left at the SDK default (off). Gemini
returns transient 503s under load, and without retries a single one fails an
entire comparison -- a five-variant request has five chances to hit one. The
Anthropic SDK retries by default; this brings the Gemini path in line.
"""

from __future__ import annotations

from typing import Any

#: 429 (rate limited) and 5xx are worth retrying; 4xx client errors are not,
#: since the same request will keep failing.
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

RETRY_ATTEMPTS = 3
INITIAL_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 8.0


def build_client(api_key: str) -> Any:
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=RETRY_ATTEMPTS,
                initial_delay=INITIAL_DELAY_SECONDS,
                max_delay=MAX_DELAY_SECONDS,
                exp_base=2,
                jitter=1.0,
                http_status_codes=RETRY_STATUS_CODES,
            ),
        ),
    )
