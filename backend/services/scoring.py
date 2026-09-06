import json
from typing import Any, Dict, List

import google.generativeai as genai

from backend.config import settings


def score_ad(
    gemini_analysis: Dict[str, Any],
    contexts: List[Dict[str, Any]],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Use Gemini text model to score the ad with retrieved context and vision findings.
    """
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required for scoring")

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.gemini_text_model)

    context_blocks = "\n\n".join(
        f"Source: {c.get('source')} | Chunk: {c.get('chunk')}\n{c.get('text')}"
        for c in contexts
    )

    prompt = (
        "You are a senior performance marketing strategist. "
        "Use the provided best-practice snippets and the Gemini image analysis to evaluate the ad. "
        "Return strict JSON with keys: scores (object with attention, clarity, targeting, cta, "
        "branding, value as 0-10 numbers), overall_score (0-10), feedback (short paragraph), "
        "recommendations (array of max 5 short bullet strings), citations (array of source filenames). "
        "Be concise and stay within the provided context.\n\n"
        f"Metadata: platform={metadata.get('platform')}, industry={metadata.get('industry')}, "
        f"ad_type={metadata.get('ad_type')}\n\n"
        f"Gemini analysis JSON:\n{json.dumps(gemini_analysis, ensure_ascii=False)}\n\n"
        f"Retrieved marketing guidance:\n{context_blocks}\n\n"
        "Now produce the JSON response."
    )

    response = model.generate_content(prompt)
    raw = response.text or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "scores": {},
            "overall_score": None,
            "feedback": raw,
            "recommendations": [],
            "citations": [],
        }
    return data

