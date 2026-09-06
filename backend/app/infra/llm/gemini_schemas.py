"""Gemini-facing response schemas.

Gemini's ``response_schema`` accepts a narrow subset of JSON Schema. The domain
models in app/domain/models.py violate it in two ways:

* ``ConfigDict(extra="forbid")`` emits ``additionalProperties``, which Gemini
  rejects outright with a 400.
* ``AdScorecard.scores`` is ``dict[Criterion, float]``, which Pydantic renders
  as a dynamic-key map (``propertyNames`` + ``$ref``). Gemini has no way to
  express that, so the six criteria have to be explicit fields.

Rather than loosen the domain model to suit one vendor's schema dialect -- the
strictness is worth keeping, and Anthropic's structured outputs actively
*require* ``additionalProperties: false`` -- the translation lives here, at the
adapter boundary. This is what the adapter layer is for.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.domain.criteria import Criterion
from backend.app.domain.models import AdScorecard, VisualAnalysis


class GeminiVisualAnalysis(BaseModel):
    """Mirror of VisualAnalysis without ``extra="forbid"``."""

    colors: list[str] = Field(default_factory=list)
    text: str = ""
    layout: str = ""
    cta: str = ""
    insights: list[str] = Field(default_factory=list)

    def to_domain(self) -> VisualAnalysis:
        return VisualAnalysis(
            colors=self.colors,
            text=self.text,
            layout=self.layout,
            cta=self.cta,
            insights=self.insights,
        )


class GeminiScores(BaseModel):
    """The six criteria as explicit fields, since Gemini cannot do key maps."""

    attention: float
    clarity: float
    targeting: float
    cta: float
    branding: float
    value: float


class GeminiScorecard(BaseModel):
    scores: GeminiScores
    overall_score: float
    feedback: str
    recommendations: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)

    def to_domain(self) -> AdScorecard:
        return AdScorecard(
            scores={
                Criterion.ATTENTION: self.scores.attention,
                Criterion.CLARITY: self.scores.clarity,
                Criterion.TARGETING: self.scores.targeting,
                Criterion.CTA: self.scores.cta,
                Criterion.BRANDING: self.scores.branding,
                Criterion.VALUE: self.scores.value,
            },
            # Clamped because the schema cannot express a numeric range, so the
            # model is free to return 11 and the domain model would reject it.
            overall_score=max(0.0, min(10.0, self.overall_score)),
            feedback=self.feedback,
            recommendations=self.recommendations[:5],
            citations=self.citations,
        )
