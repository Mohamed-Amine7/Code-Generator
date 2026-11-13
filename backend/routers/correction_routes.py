import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from core import config
from core.errors import GenerationBusy
from core.ratelimit import limiter
from core.security import get_current_user
from models import User
from schemas.feedback import CorrectionResponse, ValidationRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/correction", tags=["correction"])


@router.post("/", response_model=CorrectionResponse)
@limiter.limit(config.RATE_HEAVY)
def correct(request: Request, payload: ValidationRequest, current_user: User = Depends(get_current_user)):
    from ai.correction import correct_code

    try:
        return correct_code(payload.code, payload.language)
    except GenerationBusy as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Correction failed")
        raise HTTPException(status_code=500, detail="Correction failed")
