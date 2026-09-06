"""Gemini vision adapter -- implements the VisionAnalyzer port."""

from __future__ import annotations

import asyncio
import io

from backend.app.domain.errors import ProviderError
from backend.app.domain.models import VisualAnalysis
from backend.app.infra.llm._json import parse_model

PROMPT = (
    "You are a marketing creative analyst. Review this ad image and return JSON "
    "with keys: colors (up to 5, hex where legible else names), text (key copy "
    "you can read), layout (composition and focal areas), cta (visible "
    "call-to-action text, empty string if none), insights (up to 3 short "
    "strength/risk observations). Respond with JSON only."
)


class GeminiVisionAnalyzer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def analyze(self, image: bytes, media_type: str) -> VisualAnalysis:
        # to_thread because google-generativeai's generate_content is blocking.
        # Calling it directly from the async endpoint (as the old code did)
        # stalled the event loop for the whole request, which made any
        # concurrent fan-out pointless.
        raw = await asyncio.to_thread(self._generate, image)
        return parse_model(raw, VisualAnalysis, provider="gemini-vision")

    def _generate(self, image: bytes) -> str | None:
        import google.generativeai as genai
        from PIL import Image, UnidentifiedImageError

        try:
            pil_image = Image.open(io.BytesIO(image))
            pil_image.load()
        except (UnidentifiedImageError, OSError) as exc:
            raise ProviderError("uploaded file is not a readable image") from exc

        try:
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model)
            return model.generate_content([PROMPT, pil_image]).text
        except Exception as exc:  # noqa: BLE001 - re-raised as a domain error
            raise ProviderError(f"gemini vision request failed: {type(exc).__name__}") from exc
