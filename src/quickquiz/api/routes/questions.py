"""Questions management API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/{question_id}")
async def get_question(question_id: str):
    """Retrieve a specific question by ID."""
    return {"message": f"Question {question_id} retrieval - to be implemented"}


@router.get("/")
async def list_questions():
    """List all questions with optional filtering."""
    return {"message": "Questions listing endpoint - to be implemented"}
