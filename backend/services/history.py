import hashlib
from typing import List, Optional

from sqlalchemy.orm import Session

from models import CodeHistory


def normalize_prompt(text: str) -> str:
    """Minuscules + espaces normalisés : 'Reverse  a String' == 'reverse a string'."""
    return " ".join((text or "").lower().split())


def prompt_hash(normalized: str, language: str) -> str:
    return hashlib.sha256(f"{language}|{normalized}".encode("utf-8")).hexdigest()


def find_existing(db: Session, user_id: int, qhash: str) -> Optional[CodeHistory]:
    return (
        db.query(CodeHistory)
        .filter(CodeHistory.user_id == user_id, CodeHistory.query_hash == qhash)
        .order_by(CodeHistory.id.desc())
        .first()
    )


def save_history(db: Session, **fields) -> CodeHistory:
    entry = CodeHistory(**fields)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_history(db: Session, user_id: int, skip: int = 0, limit: int = 20, favorites_only: bool = False) -> List[CodeHistory]:
    q = db.query(CodeHistory).filter(CodeHistory.user_id == user_id)
    if favorites_only:
        q = q.filter(CodeHistory.is_favorite.is_(True))
    return q.order_by(CodeHistory.id.desc()).offset(skip).limit(limit).all()


def get_owned(db: Session, user_id: int, item_id: int) -> Optional[CodeHistory]:
    return db.query(CodeHistory).filter(CodeHistory.id == item_id, CodeHistory.user_id == user_id).first()
