"""Validation, feedback utilisateur (persisté) — toutes les routes exigent une authentification."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ai.validation import validate_code
from core import config
from core.ratelimit import limiter
from core.security import get_current_user
from database import get_db
from models import CodeValidation, Feedback, User
from schemas.feedback import Annotation, FeedbackRequest, FeedbackResponse, ValidationRequest, ValidationResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/validate", response_model=ValidationResponse)
@limiter.limit(config.RATE_HEAVY)
def validate(request: Request, body: ValidationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = validate_code(body.code, body.language)
    except Exception:
        logger.exception("Validation failed")
        raise HTTPException(status_code=500, detail="Validation failed")
    db.add(CodeValidation(user_id=current_user.id, language=result["language"],
                          quality_score=result["quality_score"], total_issues=result["total_issues"]))
    db.commit()
    return ValidationResponse(
        valid=result["valid"], quality_score=result["quality_score"],
        annotations=[Annotation(**a) for a in result["annotations"]],
        total_issues=result["total_issues"], language=result["language"], tools=result["tools"],
    )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(body: FeedbackRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = Feedback(user_id=current_user.id, code_id=body.code_id, type=body.type.value, comment=body.comment, rating=body.rating)
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackResponse(success=True, message="Feedback enregistré avec succès", feedback_id=str(row.id))


@router.get("/feedbacks/{code_id}")
def get_feedbacks(code_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Feedback).filter(Feedback.user_id == current_user.id, Feedback.code_id == code_id).order_by(Feedback.id.desc()).all()
    return {
        "code_id": code_id, "total": len(rows),
        "feedbacks": [{"id": r.id, "type": r.type, "comment": r.comment, "rating": r.rating,
                       "timestamp": r.created_at.isoformat() if r.created_at else None} for r in rows],
    }
