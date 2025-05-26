"""Question generation API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/generate", tags=["generation"])


@router.post("/")
async def generate_questions():
    """Generate quiz questions from ingested content."""
    return {"message": "Question generation endpoint - to be implemented"}
