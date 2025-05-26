"""Document ingestion API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
async def ingest_document():
    """Ingest a document (PDF or URL) for question generation."""
    return {"message": "Document ingestion endpoint - to be implemented"}
