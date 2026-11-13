# backend/models.py
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    code_histories = relationship("CodeHistory", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")


class CodeHistory(Base):
    __tablename__ = "code_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    query = Column(Text, nullable=False)                      # prompt d'origine (ex: en français)
    translated_query = Column(Text, nullable=True)            # prompt envoyé au modèle (anglais)
    source_language = Column(String(10), nullable=True)       # 'en' | 'fr' | 'ar' | 'code'
    query_hash = Column(String(64), nullable=True, index=True)  # sha256(langage + prompt normalisé) -> cache
    generated_code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)
    is_favorite = Column(Boolean, nullable=False, default=False, server_default="0")
    verified = Column(String(20), nullable=True)              # passed | failed | repaired | skipped
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="code_histories")


class CodeValidation(Base):
    __tablename__ = "code_validations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    language = Column(String(20))
    quality_score = Column(Float)
    total_issues = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    code_id = Column(String(100), index=True)
    type = Column(String(20))
    comment = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="feedbacks")
