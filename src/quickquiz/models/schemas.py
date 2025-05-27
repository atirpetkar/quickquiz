"""Pydantic schemas for request/response models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class QuestionType(str, Enum):
    """Question type enumeration."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SourceType(str, Enum):
    """Source type enumeration."""

    PDF = "pdf"
    URL = "url"
    TEXT = "text"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configurations."""

    class Config:
        from_attributes = True


# Document schemas
class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    title: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    source_url: HttpUrl | None = None
    content: str | None = None
    metadata: dict[str, Any] | None = None


class DocumentResponse(BaseSchema):
    """Schema for document response."""

    id: uuid.UUID
    title: str
    source_type: str
    source_url: str | None
    content_hash: str
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime | None


# Question schemas
class QuestionOption(BaseModel):
    """Schema for question options."""

    label: str = Field(..., pattern="^[A-D]$")
    text: str = Field(..., min_length=1)


class QuestionCreate(BaseModel):
    """Schema for creating a question."""

    document_id: uuid.UUID
    question_text: str = Field(..., min_length=10)
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: list[QuestionOption] | None = None
    correct_answer: str = Field(..., min_length=1)
    explanation: str | None = None
    difficulty_level: DifficultyLevel | None = None
    bloom_level: str | None = None
    topic: str | None = None


class QuestionResponse(BaseSchema):
    """Schema for question response."""

    id: uuid.UUID
    document_id: uuid.UUID
    question_text: str
    question_type: str
    options: list[dict[str, str]] | None
    correct_answer: str
    explanation: str | None
    difficulty_level: str | None
    bloom_level: str | None
    topic: str | None
    quality_score: float | None
    is_approved: bool
    created_at: datetime
    updated_at: datetime | None


# Generation request schemas
class GenerationRequest(BaseModel):
    """Schema for question generation request."""

    document_id: uuid.UUID
    num_questions: int = Field(default=5, ge=1, le=50)
    difficulty_level: DifficultyLevel | None = None
    question_types: list[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE])
    topics: list[str] | None = None


class GenerationResponse(BaseModel):
    """Schema for generation response."""

    job_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    num_questions_requested: int
    questions: list[QuestionResponse] | None = None
    created_at: datetime


# Evaluation schemas
class EvaluationRequest(BaseModel):
    """Schema for question evaluation request."""

    question_id: uuid.UUID | None = None
    question_text: str | None = None
    options: list[QuestionOption] | None = None
    correct_answer: str | None = None
    explanation: str | None = None


class EvaluationResponse(BaseModel):
    """Schema for evaluation response."""

    quality_score: float = Field(..., ge=0, le=100)
    is_approved: bool
    feedback: dict[str, Any]
    suggestions: list[str]
    issues: list[str]


# Ingestion schemas
class IngestionRequest(BaseModel):
    """Schema for document ingestion request."""

    title: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    source_url: HttpUrl | None = None
    content: str | None = None
    metadata: dict[str, Any] | None = None


class IngestionResponse(BaseModel):
    """Schema for ingestion response."""

    job_id: uuid.UUID
    document: DocumentResponse
    status: str
    chunks_created: int | None = None
    message: str


# List response schemas
class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""

    items: list[Any]
    total: int
    page: int
    size: int
    pages: int


class DocumentListResponse(PaginatedResponse):
    """Schema for document list response."""

    items: list[DocumentResponse]


class QuestionListResponse(PaginatedResponse):
    """Schema for question list response."""

    items: list[QuestionResponse]


# Error schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    detail: str | None = None
    code: str | None = None
