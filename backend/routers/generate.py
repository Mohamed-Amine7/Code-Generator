import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ai.textutils import normalize_language
from ai.translate import to_english
from core import config
from core.errors import GenerationBusy
from core.ratelimit import limiter
from core.security import get_current_user
from database import SessionLocal, get_db
from models import User
from schemas.ai_schemas import CodeResponse, HistoryItem, InputText
from services.history import find_existing, get_owned, list_history, normalize_prompt, prompt_hash, save_history

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generate"])

PROMPTS = [
    "Create a calculator in Python",
    "Reverse a string in Python",
    "Find the maximum number in a list",
]


@router.get("/prompts")
def get_prompts():
    return PROMPTS


def _prepare(payload: InputText):
    """Traduit vers l'anglais (fr/ar) puis calcule la clé de cache sur le prompt normalisé."""
    english, source = to_english(payload.text)
    lang = normalize_language(payload.language)
    return english, source, lang, prompt_hash(normalize_prompt(english), lang)


def _is_bad_cached_code(code: str, lang: str) -> bool:
    """Ignore les anciens résultats bogués en cache (ex: 'Hello, World!' généré pour du Java)."""
    if not code or len(code.strip()) < 10:
        return True
    if lang == "java" and ("Hello, World!" in code or "void main(" in code):
        return True
    return False


def _response(entry, cached: bool, verification=None) -> CodeResponse:
    return CodeResponse(
        id=entry.id, generated_code=entry.generated_code, explanation=entry.explanation or "",
        language=entry.language, cached=cached, source_language=entry.source_language,
        verification=verification or ({"status": entry.verified} if entry.verified else None),
    )


@router.post("/generate", response_model=CodeResponse)
@limiter.limit(config.RATE_HEAVY)
def generate(request: Request, payload: InputText, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    english, source, lang, qhash = _prepare(payload)

    if not payload.regenerate:
        existing = find_existing(db, current_user.id, qhash)
        if existing and not _is_bad_cached_code(existing.generated_code, lang):
            return _response(existing, cached=True)

    try:
        from ai.generator import generate_with_ai

        code = generate_with_ai(english, lang)
        verification = None
        if payload.verify and lang == "python":
            from ai.verify import verify_and_repair

            code, verification = verify_and_repair(code, english)
    except GenerationBusy as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Code generation failed")
        raise HTTPException(status_code=500, detail="Code generation failed. Check the server logs.")

    entry = save_history(
        db, user_id=current_user.id, query=payload.text, translated_query=english, source_language=source,
        query_hash=qhash, generated_code=code, explanation="", language=lang,
        verified=(verification or {}).get("status"),
    )
    return _response(entry, cached=False, verification=verification)


@router.post("/generate/stream")
@limiter.limit(config.RATE_HEAVY)
def generate_stream(request: Request, payload: InputText, current_user: User = Depends(get_current_user)):
    """Server-Sent Events : {"token": "..."} en continu, puis {"done": true, "code": "...", "id": n}."""
    english, source, lang, qhash = _prepare(payload)
    user_id = current_user.id

    def event(obj) -> str:
        return f"data: {json.dumps(obj)}\n\n"

    def stream():
        db = SessionLocal()  # session propre : celle de la dépendance peut être fermée avant la fin du flux
        try:
            if not payload.regenerate:
                existing = find_existing(db, user_id, qhash)
                if existing and not _is_bad_cached_code(existing.generated_code, lang):
                    yield event({"done": True, "code": existing.generated_code, "id": existing.id, "cached": True,
                                 "source_language": existing.source_language})
                    return
            from ai.generator import stream_generate

            final = ""
            for kind, value in stream_generate(english, lang):
                if kind == "token":
                    yield event({"token": value})
                else:
                    final = value
            entry = save_history(
                db, user_id=user_id, query=payload.text, translated_query=english, source_language=source,
                query_hash=qhash, generated_code=final, explanation="", language=lang,
            )
            yield event({"done": True, "code": final, "id": entry.id, "cached": False, "source_language": source})
        except GenerationBusy as exc:
            yield event({"error": str(exc)})
        except Exception:
            logger.exception("Streaming generation failed")
            yield event({"error": "Code generation failed. Check the server logs."})
        finally:
            db.close()

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ------------------------------------------------------------------ historique
@router.get("/history", response_model=List[HistoryItem])
def get_history(skip: int = 0, limit: int = 20, favorites_only: bool = False,
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    return list_history(db, current_user.id, max(0, skip), limit, favorites_only)


@router.delete("/history/{item_id}", status_code=204)
def delete_history(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_owned(db, current_user.id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    db.delete(item)
    db.commit()


@router.patch("/history/{item_id}/favorite", response_model=HistoryItem)
def toggle_favorite(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_owned(db, current_user.id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    item.is_favorite = not item.is_favorite
    db.commit()
    db.refresh(item)
    return item
