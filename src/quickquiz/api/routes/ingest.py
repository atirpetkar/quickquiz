"""Document ingestion API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import DocumentIngestionError
from ...models.schemas import (
    DocumentCreate,
    DocumentResponse,
    IngestionRequest,
    IngestionResponse,
    SourceType,
)
from ...services.embeddings import EmbeddingService
from ...services.ingestor import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_ingestion_service() -> IngestionService:
    """Get ingestion service instance."""
    embedding_service = EmbeddingService()
    return IngestionService(embedding_service)


@router.post("/upload", response_model=IngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """Upload and ingest a PDF document."""

    # Validate file type
    if not file.content_type or "pdf" not in file.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for upload",
        )

    # Validate file size (50MB limit)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit",
        )

    # Reset file pointer
    await file.seek(0)

    try:
        # Use filename as title if not provided
        document_title = title or file.filename or "Uploaded Document"

        # Parse metadata if provided
        doc_metadata = {}
        if metadata:
            try:
                import json

                doc_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format for metadata",
                )

        # Add upload metadata
        doc_metadata.update(
            {
                "original_filename": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type,
                "upload_method": "file_upload",
            }
        )

        # Create temporary file and extract content
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()

            try:
                # Extract content from uploaded file
                from ...utils.pdf_parser import PDFParser

                pdf_parser = PDFParser()
                content = await pdf_parser.extract_from_file(tmp_file.name)

                # Create document record
                document_data = DocumentCreate(
                    title=document_title,
                    source_type=SourceType.PDF,
                    content=content,
                    metadata=doc_metadata,
                )

                # Ingest document
                document = await ingestion_service.ingest_document(db, document_data)

                return IngestionResponse(
                    job_id=uuid.uuid4(),  # For future async processing
                    document=DocumentResponse(
                        id=document.id,
                        title=document.title,
                        source_type=document.source_type,
                        source_url=document.source_url,
                        content_hash=document.content_hash,
                        metadata=document.metadata,
                        created_at=document.created_at,
                        updated_at=document.updated_at,
                    ),
                    status="completed",
                    chunks_created=len(await ingestion_service._create_chunks(content)),
                    message="Document uploaded and processed successfully",
                )

            finally:
                # Clean up temporary file
                os.unlink(tmp_file.name)

    except DocumentIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file upload: {str(e)}",
        )


@router.post("/ingest-url", response_model=IngestionResponse)
async def ingest_from_url(
    request: IngestionRequest,
    db: AsyncSession = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """Ingest content from a URL (web page or PDF)."""

    if not request.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Source URL is required"
        )

    try:
        # Add request metadata
        doc_metadata = request.metadata or {}
        doc_metadata.update(
            {"ingestion_method": "url", "source_url": str(request.source_url)}
        )

        # Create document data
        document_data = DocumentCreate(
            title=request.title,
            source_type=request.source_type,
            source_url=request.source_url,
            content=request.content,
            metadata=doc_metadata,
        )

        # Ingest document
        document = await ingestion_service.ingest_document(db, document_data)

        # Count chunks
        chunks_count = (
            len(document.chunks)
            if hasattr(document, "chunks") and document.chunks
            else 0
        )

        return IngestionResponse(
            job_id=uuid.uuid4(),  # For future async processing
            document=DocumentResponse(
                id=document.id,
                title=document.title,
                source_type=document.source_type,
                source_url=document.source_url,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            ),
            status="completed",
            chunks_created=chunks_count,
            message="URL content ingested successfully",
        )

    except DocumentIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during URL ingestion: {str(e)}",
        )


@router.post("/ingest-text", response_model=IngestionResponse)
async def ingest_text_content(
    request: IngestionRequest,
    db: AsyncSession = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """Ingest text content directly."""

    if not request.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is required for text ingestion",
        )

    if len(request.content.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content must be at least 50 characters long",
        )

    try:
        # Add request metadata
        doc_metadata = request.metadata or {}
        doc_metadata.update(
            {"ingestion_method": "text", "content_length": len(request.content)}
        )

        # Create document data
        document_data = DocumentCreate(
            title=request.title,
            source_type=SourceType.TEXT,
            content=request.content,
            metadata=doc_metadata,
        )

        # Ingest document
        document = await ingestion_service.ingest_document(db, document_data)

        # Count chunks
        chunks_count = (
            len(document.chunks)
            if hasattr(document, "chunks") and document.chunks
            else 0
        )

        return IngestionResponse(
            job_id=uuid.uuid4(),  # For future async processing
            document=DocumentResponse(
                id=document.id,
                title=document.title,
                source_type=document.source_type,
                source_url=document.source_url,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            ),
            status="completed",
            chunks_created=chunks_count,
            message="Text content ingested successfully",
        )

    except DocumentIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during text ingestion: {str(e)}",
        )


@router.get("/{document_id}/status", response_model=DocumentResponse)
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """Get the status of an ingested document."""

    try:
        # Validate UUID format
        uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    try:
        document = await ingestion_service.get_document_status(db, document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        return DocumentResponse(
            id=document.id,
            title=document.title,
            source_type=document.source_type,
            source_url=document.source_url,
            content_hash=document.content_hash,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document status: {str(e)}",
        )


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all ingested documents with optional filtering."""

    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Limit cannot exceed 1000"
        )

    try:
        from sqlalchemy import select

        from ...models.database import Document

        # Build query
        stmt = select(Document).offset(skip).limit(limit)

        if source_type:
            stmt = stmt.where(Document.source_type == source_type)

        # Execute query
        result = await db.execute(stmt)
        documents = result.scalars().all()

        return [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                source_type=doc.source_type,
                source_url=doc.source_url,
                content_hash=doc.content_hash,
                metadata=doc.metadata,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}",
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and all its associated data."""

    try:
        # Validate UUID format
        uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    try:
        from sqlalchemy import delete, select

        from ...models.database import Document, DocumentChunk, Question

        # Check if document exists
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Delete related data (cascading should handle this, but being explicit)
        await db.execute(delete(Question).where(Question.document_id == document_id))
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        await db.execute(delete(Document).where(Document.id == document_id))

        await db.commit()

        return {"message": "Document deleted successfully", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}",
        )
