import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from ai.translate import to_english
from core import config
from core.errors import GenerationBusy
from core.ratelimit import limiter
from core.security import get_current_user
from models import User
from schemas.ai_schemas import AnalyzeRequest, CodeRequest
from services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analyze"])


def _guard(fn):
    try:
        return fn()
    except GenerationBusy as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("AI call failed")
        raise HTTPException(status_code=500, detail="AI processing failed. Check the server logs.")


@router.post("/analyze")
@limiter.limit(config.RATE_HEAVY)
def analyze(request: Request, req: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    """Réponse : {intent: str, score, confidence, scores: {label: p}, method, source_language, translated_text, cached: bool}."""
    cache_key = req.text.strip().lower()
    hit = get_cached("intent", cache_key)
    if hit is not None:
        return {**hit, "cached": True}

    from ai.analyze import analyze_text

    english, source = to_english(req.text)

    def run():
        result = analyze_text(english)
        result["source_language"] = source
        result["translated_text"] = english if english != req.text else None
        result["cached"] = False
        return result

    data = _guard(run)
    set_cached("intent", cache_key, data)
    return data


@router.post("/code/explain")
@limiter.limit(config.RATE_HEAVY)
def explain(request: Request, req: CodeRequest, current_user: User = Depends(get_current_user)):
    key = f"{req.level}:" + req.code.strip()
    hit = get_cached("explain", key)
    if hit is not None:
        return {"explanation": hit, "cached": True}

    from ai.explain import explain_code

    result = _guard(lambda: explain_code(req.code, req.level))
    set_cached("explain", key, result)
    return {"explanation": result, "cached": False}


@router.post("/code/feedback")
@limiter.limit(config.RATE_HEAVY)
def feedback(request: Request, req: CodeRequest, current_user: User = Depends(get_current_user)):
    lang = req.language or "python"
    key = f"{lang}:" + req.code.strip()
    hit = get_cached("feedback", key)
    if hit is not None:
        return {"feedback": hit, "cached": True}

    from ai.feedback import give_feedback

    result = _guard(lambda: give_feedback(req.code, lang))
    set_cached("feedback", key, result)
    return {"feedback": result, "cached": False}


@router.post("/code/tests")
@limiter.limit(config.RATE_HEAVY)
def tests(request: Request, req: CodeRequest, current_user: User = Depends(get_current_user)):
    key = req.code.strip()
    hit = get_cached("tests", key)
    if hit is not None:
        return {"tests": hit, "cached": True}

    from ai.testgen import generate_tests

    result = _guard(lambda: generate_tests(req.code))
    set_cached("tests", key, result)
    return {"tests": result, "cached": False}
