"""Prompt construction, shared across providers.

Kept out of the adapters so the two providers are genuinely comparable: if the
Gemini and Claude scorers disagree, it is the model differing, not the prompt.
Bump ``Settings.prompt_version`` whenever anything here changes -- it is part of
the assessment cache key.
"""

from __future__ import annotations

import json

from backend.app.domain.criteria import RUBRICS, Criterion
from backend.app.domain.models import AdMetadata, RetrievedChunk, VisualAnalysis

SYSTEM_INSTRUCTION = (
    "You are a senior performance marketing strategist. Judge the ad using the "
    "supplied best-practice passages and the vision analysis. Ground every claim "
    "in the passages provided; do not invent guidance. Be concise and specific."
)


def _rubric_block() -> str:
    return "\n".join(f"- {c.value}: {RUBRICS[c]}" for c in Criterion)


def _context_block(context: list[RetrievedChunk]) -> str:
    if not context:
        return "(no guidance retrieved)"
    return "\n\n".join(
        f"Source: {chunk.source} | Chunk: {chunk.chunk}\n{chunk.text}"
        for chunk in context
    )


def build_scoring_prompt(
    analysis: VisualAnalysis,
    context: list[RetrievedChunk],
    metadata: AdMetadata,
) -> str:
    return f"""{SYSTEM_INSTRUCTION}

Placement:
platform={metadata.platform}, industry={metadata.industry}, ad_type={metadata.ad_type}

Score every one of these six criteria from 0 to 10. All six are required.
{_rubric_block()}

Vision analysis of the creative:
{json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2)}

Retrieved marketing guidance:
{_context_block(context)}

Return JSON only, with keys: scores (an object with all six criterion names as
keys and numbers 0-10 as values), overall_score (number 0-10), feedback (one
short paragraph), recommendations (array of at most 5 short strings), citations
(array of the source filenames you actually relied on).
"""
