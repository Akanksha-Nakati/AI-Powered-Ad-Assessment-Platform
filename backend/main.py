import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.services.image_analyzer import analyze_image
from backend.services.rag import load_vectorstore, retrieve_context, serialize_docs
from backend.services.scoring import score_ad

app = FastAPI(title="Ad Assessment API", version="0.1.0")

origins = ["*"]
if settings.frontend_origin:
    origins = [settings.frontend_origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache the vector store on startup
vectorstore_ready = False


@app.on_event("startup")
async def startup_event() -> None:
    global vectorstore_ready
    try:
        # Run in thread executor since Chroma/OpenAI can be blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, load_vectorstore)
        vectorstore_ready = True
    except Exception as exc:  # pragma: no cover - startup logging only
        print(f"[startup] failed to initialize vector store: {exc}")
        vectorstore_ready = False


@app.get("/health")
async def health() -> Dict[str, Any]:
    docs_exist = settings.docs_path.exists() and any(settings.docs_path.glob("*.md"))
    store_exists = settings.chroma_path.exists() and any(settings.chroma_path.glob("**/*"))
    return {
        "status": "ok",
        "vectorstore_ready": vectorstore_ready,
        "docs_exist": docs_exist,
        "store_exists": store_exists,
    }


def _validate_keys() -> None:
    missing = []
    if not settings.google_api_key:
        missing.append("GOOGLE_API_KEY")
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required API keys: {', '.join(missing)}",
        )


@app.post("/assess")
async def assess_ad(
    ad_image: UploadFile = File(...),
    platform: str = Form(...),
    industry: str = Form(...),
    ad_type: str = Form(...),
) -> JSONResponse:
    _validate_keys()

    if not vectorstore_ready:
        raise HTTPException(status_code=503, detail="Vector store not ready")

    try:
        image_bytes = await ad_image.read()
        gemini_analysis = analyze_image(image_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini analysis failed: {exc}") from exc

    query = (
        f"Best practices for {platform} ads in {industry} for {ad_type}. "
        f"Consider CTA, color, clarity, attention. "
        f"Image notes: {gemini_analysis}"
    )

    try:
        contexts = retrieve_context(query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {exc}") from exc

    serialized_contexts = serialize_docs(contexts)
    try:
        claude_result = score_ad(
            gemini_analysis=gemini_analysis,
            contexts=serialized_contexts,
            metadata={"platform": platform, "industry": industry, "ad_type": ad_type},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {exc}") from exc

    scores = claude_result.get("scores", {})
    overall = claude_result.get("overall_score")
    if overall is None and scores:
        overall = round(sum(scores.values()) / len(scores), 2)

    response = {
        "scores": scores,
        "overall_score": overall,
        "feedback": claude_result.get("feedback", ""),
        "recommendations": claude_result.get("recommendations", []),
        "citations": claude_result.get("citations", []),
        "context": serialized_contexts,
        "gemini": gemini_analysis,
    }
    return JSONResponse(content=response)

