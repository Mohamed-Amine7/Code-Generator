from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    SUGGESTION = "suggestion"


class Annotation(BaseModel):
    line: int = Field(default=0, description="Numéro de ligne (0 = global)")
    type: str
    severity: str = "info"
    message: str
    source: str = ""


class ValidationRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20000)
    language: str = "python"
    code_id: Optional[str] = None


class ValidationResponse(BaseModel):
    valid: bool
    quality_score: float
    annotations: List[Annotation] = []
    total_issues: int
    language: str
    tools: List[str] = []


class CorrectionResponse(BaseModel):
    original_code: str
    corrected_code: str
    diff: str
    fixes: List[str]
    changed: bool
    language: str
    tools: List[str] = []


class FeedbackRequest(BaseModel):
    code_id: str = Field(..., max_length=100)
    type: FeedbackType
    comment: Optional[str] = Field(None, max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5)


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[str] = None
