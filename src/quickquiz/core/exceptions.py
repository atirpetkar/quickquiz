"""Custom exceptions for QuickQuiz-GPT."""

from fastapi import HTTPException


class QuickQuizException(Exception):
    """Base exception for QuickQuiz-GPT."""
    pass


class DocumentIngestionError(QuickQuizException):
    """Exception raised during document ingestion."""
    pass


class QuestionGenerationError(QuickQuizException):
    """Exception raised during question generation."""
    pass


class EvaluationError(QuickQuizException):
    """Exception raised during question evaluation."""
    pass


class DatabaseError(QuickQuizException):
    """Exception raised during database operations."""
    pass


class CacheError(QuickQuizException):
    """Exception raised during cache operations."""
    pass


# HTTP Exceptions
class DocumentNotFoundError(HTTPException):
    """Document not found exception."""
    def __init__(self, document_id: str):
        super().__init__(
            status_code=404, 
            detail=f"Document with ID {document_id} not found"
        )


class QuestionNotFoundError(HTTPException):
    """Question not found exception."""
    def __init__(self, question_id: str):
        super().__init__(
            status_code=404, 
            detail=f"Question with ID {question_id} not found"
        )
