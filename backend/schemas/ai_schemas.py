from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_LANGUAGES = ("python", "java")


class InputText(BaseModel):
    text: str = Field(..., min_length=3, max_length=1000)
    language: str = "python"
    verify: bool = False        # génère des tests, les exécute en sandbox et répare une fois si besoin
    regenerate: bool = False    # ignore le cache de l'historique

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("text is too short")
        return v

    @field_validator("language")
    @classmethod
    def supported_language(cls, v: str) -> str:
        v = (v or "python").strip().lower()
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language '{v}'. Supported: {', '.join(SUPPORTED_LANGUAGES)}")
        return v


class CodeResponse(BaseModel):
    id: Optional[int] = None
    generated_code: str
    explanation: str = ""
    language: str
    success: bool = True
    cached: bool = False
    source_language: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None


class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20000)
    level: Optional[str] = "beginner"
    language: Optional[str] = "python"


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    query: str
    generated_code: str
    explanation: Optional[str] = None
    language: Optional[str] = None
    source_language: Optional[str] = None
    is_favorite: bool = False
    verified: Optional[str] = None
    timestamp: Optional[datetime] = None
