"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


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
    source_url: Optional[HttpUrl] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseSchema):
    """Schema for document response."""
    id: uuid.UUID
    title: str
    source_type: str
    source_url: Optional[str]
    content_hash: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]


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
    options: Optional[List[QuestionOption]] = None
    correct_answer: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    bloom_level: Optional[str] = None
    topic: Optional[str] = None


class QuestionResponse(BaseSchema):
    """Schema for question response."""
    id: uuid.UUID
    document_id: uuid.UUID
    question_text: str
    question_type: str
    options: Optional[List[Dict[str, str]]]
    correct_answer: str
    explanation: Optional[str]
    difficulty_level: Optional[str]
    bloom_level: Optional[str]
    topic: Optional[str]
    quality_score: Optional[float]
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime]


# Generation request schemas
class GenerationRequest(BaseModel):
    """Schema for question generation request."""
    document_id: uuid.UUID
    num_questions: int = Field(default=5, ge=1, le=50)
    difficulty_level: Optional[DifficultyLevel] = None
    question_types: List[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE])
    topics: Optional[List[str]] = None


class GenerationResponse(BaseModel):
    """Schema for generation response."""
    job_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    num_questions_requested: int
    questions: Optional[List[QuestionResponse]] = None
    created_at: datetime


# Evaluation schemas
class EvaluationRequest(BaseModel):
    """Schema for question evaluation request."""
    question_id: Optional[uuid.UUID] = None
    question_text: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Schema for evaluation response."""
    quality_score: float = Field(..., ge=0, le=100)
    is_approved: bool
    feedback: Dict[str, Any]
    suggestions: List[str]
    issues: List[str]


# Ingestion schemas
class IngestionRequest(BaseModel):
    """Schema for document ingestion request."""
    title: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    source_url: Optional[HttpUrl] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IngestionResponse(BaseModel):
    """Schema for ingestion response."""
    job_id: uuid.UUID
    document: DocumentResponse
    status: str
    chunks_created: Optional[int] = None
    message: str


# List response schemas
class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


class DocumentListResponse(PaginatedResponse):
    """Schema for document list response."""
    items: List[DocumentResponse]


class QuestionListResponse(PaginatedResponse):
    """Schema for question list response."""
    items: List[QuestionResponse]


# Error schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
