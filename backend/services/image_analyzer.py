import io
import json
from typing import Dict, Any

import google.generativeai as genai
from PIL import Image

from backend.config import settings


def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Send the ad image to Gemini and ask for structured analysis.
    """
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required for image analysis")

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    image = Image.open(io.BytesIO(image_bytes))

    prompt = (
        "You are a marketing creative analyst. Review this ad image and return JSON with "
        "keys: colors (top 5 as hex if visible, else names), text (detected key copy), "
        "layout (brief description of composition and focal areas), cta (visible call-to-action text), "
        "insights (3 bullet insights about strengths/risks). Respond only with JSON."
    )

    response = model.generate_content([prompt, image])
    text = response.text or "{}"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: wrap raw text if Gemini didn't return JSON
        return {
            "raw": text,
            "colors": [],
            "text": "",
            "layout": "",
            "cta": "",
            "insights": [],
        }

