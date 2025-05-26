"""Document ingestion service."""

import hashlib
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import Document, DocumentChunk
from ..models.schemas import DocumentCreate, SourceType
from ..core.exceptions import DocumentIngestionError
from .embeddings import EmbeddingService
from ..utils.text_processor import TextProcessor
from ..utils.pdf_parser import PDFParser


class IngestionService:
    """Service for ingesting documents and creating embeddings."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.text_processor = TextProcessor()
        self.pdf_parser = PDFParser()
    
    async def ingest_document(
        self, 
        db: AsyncSession, 
        document_data: DocumentCreate
    ) -> Document:
        """Ingest a document and create chunks with embeddings."""
        
        try:
            # Extract content based on source type
            content = await self._extract_content(document_data)
            
            # Create content hash for deduplication
            content_hash = self._create_content_hash(content)
            
            # Check if document already exists
            existing_doc = await self._find_existing_document(db, content_hash)
            if existing_doc:
                return existing_doc
            
            # Create document record
            document = Document(
                title=document_data.title,
                source_type=document_data.source_type.value,
                source_url=str(document_data.source_url) if document_data.source_url else None,
                content_hash=content_hash,
                metadata=document_data.metadata or {}
            )
            
            db.add(document)
            await db.flush()  # Get the document ID
            
            # Process content into chunks
            chunks = await self._create_chunks(content)
            
            # Create embeddings for chunks
            await self._create_chunk_embeddings(db, document.id, chunks)
            
            await db.commit()
            return document
            
        except Exception as e:
            await db.rollback()
            raise DocumentIngestionError(f"Failed to ingest document: {str(e)}")
    
    async def _extract_content(self, document_data: DocumentCreate) -> str:
        """Extract content from different source types."""
        
        if document_data.source_type == SourceType.TEXT:
            if not document_data.content:
                raise DocumentIngestionError("Content is required for text source type")
            return document_data.content
        
        elif document_data.source_type == SourceType.PDF:
            if not document_data.source_url:
                raise DocumentIngestionError("Source URL is required for PDF source type")
            return await self.pdf_parser.extract_from_url(str(document_data.source_url))
        
        elif document_data.source_type == SourceType.URL:
            if not document_data.source_url:
                raise DocumentIngestionError("Source URL is required for URL source type")
            # TODO: Implement web scraping with trafilatura
            raise DocumentIngestionError("URL ingestion not yet implemented")
        
        else:
            raise DocumentIngestionError(f"Unsupported source type: {document_data.source_type}")
    
    def _create_content_hash(self, content: str) -> str:
        """Create a hash of the content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _find_existing_document(self, db: AsyncSession, content_hash: str) -> Optional[Document]:
        """Check if a document with the same content hash already exists."""
        # TODO: Implement database query
        return None
    
    async def _create_chunks(self, content: str) -> List[str]:
        """Split content into chunks for processing."""
        return await self.text_processor.chunk_text(content)
    
    async def _create_chunk_embeddings(self, db: AsyncSession, document_id: str, chunks: List[str]):
        """Create chunk records with embeddings."""
        
        for i, chunk_content in enumerate(chunks):
            # Generate embedding
            embedding = await self.embedding_service.generate_embedding(chunk_content)
            
            # Create chunk record
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk_content,
                embedding=embedding,
                token_count=len(chunk_content.split()),  # Rough token count
                metadata={"chunk_type": "text"}
            )
            
            db.add(chunk)
