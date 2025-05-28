"""Document ingestion service."""

import hashlib
import logging
from typing import Optional

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    # Fallback for development
    select = None
    AsyncSession = None

from ..core.exceptions import DocumentIngestionError
from ..models.database import Document, DocumentChunk
from ..models.schemas import DocumentCreate, SourceType
from ..utils.pdf_parser import PDFParser
from ..utils.text_processor import TextProcessor
from ..utils.url_extractor import URLExtractor
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting documents and creating embeddings."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.text_processor = TextProcessor()
        self.pdf_parser = PDFParser()

    async def ingest_document(
        self, db: AsyncSession, document_data: DocumentCreate
    ) -> Document:
        """Ingest a document and create chunks with embeddings."""

        logger.info(f"Starting ingestion for document: {document_data.title}")

        try:
            # Extract content based on source type
            content = await self._extract_content(document_data)

            if not content or len(content.strip()) < 50:
                raise DocumentIngestionError(
                    "Extracted content is too short (minimum 50 characters required)"
                )

            # Create content hash for deduplication
            content_hash = self._create_content_hash(content)
            logger.debug(f"Content hash: {content_hash}")

            # Check if document already exists
            existing_doc = await self._find_existing_document(db, content_hash)
            if existing_doc:
                logger.info(f"Document already exists with ID: {existing_doc.id}")
                return existing_doc

            # Create document record
            document = Document(
                title=document_data.title,
                source_type=document_data.source_type.value,
                source_url=str(document_data.source_url)
                if document_data.source_url
                else None,
                content_hash=content_hash,
                metadata=document_data.metadata or {},
            )

            db.add(document)
            await db.flush()  # Get the document ID
            logger.info(f"Created document record with ID: {document.id}")

            # Process content into chunks
            chunks = await self._create_chunks(content)
            logger.info(f"Created {len(chunks)} chunks")

            if not chunks:
                raise DocumentIngestionError("No valid chunks created from content")

            # Create embeddings for chunks
            await self._create_chunk_embeddings(db, document.id, chunks)
            logger.info(f"Generated embeddings for {len(chunks)} chunks")

            await db.commit()
            logger.info(f"Successfully ingested document: {document.id}")
            return document

        except DocumentIngestionError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error during document ingestion: {e}")
            raise DocumentIngestionError(f"Failed to ingest document: {str(e)}")

    async def _extract_content(self, document_data: DocumentCreate) -> str:
        """Extract content from different source types."""
        try:
            if document_data.source_type == SourceType.TEXT:
                return await self._extract_text_content(document_data)
            elif document_data.source_type == SourceType.PDF:
                return await self._extract_pdf_content(document_data)
            elif document_data.source_type == SourceType.URL:
                return await self._extract_url_content(document_data)
            else:
                raise DocumentIngestionError(
                    f"Unsupported source type: {document_data.source_type}"
                )
        except DocumentIngestionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during content extraction: {e}")
            raise DocumentIngestionError(f"Failed to extract content: {str(e)}")

    async def _extract_text_content(self, document_data: DocumentCreate) -> str:
        """Extract content from text source."""
        if not document_data.content:
            raise DocumentIngestionError("Content is required for text source type")
        return document_data.content

    async def _extract_pdf_content(self, document_data: DocumentCreate) -> str:
        """Extract content from PDF source."""
        if not document_data.source_url:
            raise DocumentIngestionError("Source URL is required for PDF source type")
        logger.info(f"Extracting content from PDF: {document_data.source_url}")
        return await self.pdf_parser.extract_from_url(str(document_data.source_url))

    async def _extract_url_content(self, document_data: DocumentCreate) -> str:
        """Extract content from URL source."""
        if not document_data.source_url:
            raise DocumentIngestionError("Source URL is required for URL source type")

        logger.info(f"Extracting content from URL: {document_data.source_url}")

        async with URLExtractor() as extractor:
            if not extractor.is_valid_url(str(document_data.source_url)):
                raise DocumentIngestionError(
                    f"Invalid or unsupported URL: {document_data.source_url}"
                )

            content = await extractor.extract_content(str(document_data.source_url))
            await self._extract_and_merge_metadata(extractor, document_data)
            return content

    async def _extract_and_merge_metadata(
        self, extractor, document_data: DocumentCreate
    ):
        """Extract and merge metadata from URL source."""
        try:
            metadata = await extractor.extract_metadata(str(document_data.source_url))
            if metadata and document_data.metadata:
                document_data.metadata.update(metadata)
            elif metadata:
                document_data.metadata = metadata
        except Exception as e:
            logger.warning(f"Failed to extract metadata from URL: {e}")

    def _create_content_hash(self, content: str) -> str:
        """Create a hash of the content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def _find_existing_document(
        self, db: AsyncSession, content_hash: str
    ) -> Optional[Document]:
        """Check if a document with the same content hash already exists."""
        try:
            stmt = select(Document).where(Document.content_hash == content_hash)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error checking for existing document: {e}")
            return None

    async def _create_chunks(self, content: str) -> list[str]:
        """Split content into chunks for processing."""
        return await self.text_processor.chunk_text(content)

    async def _create_chunk_embeddings(
        self, db: AsyncSession, document_id: str, chunks: list[str]
    ):
        """Create chunk records with embeddings."""

        # Process chunks in batches for better performance
        batch_size = 10

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]

            try:
                # Generate embeddings for batch
                embeddings = await self.embedding_service.generate_embeddings_batch(
                    batch_chunks
                )

                # Create chunk records
                for j, (chunk_content, embedding) in enumerate(
                    zip(batch_chunks, embeddings, strict=False)
                ):
                    chunk_index = i + j

                    # Estimate token count more accurately
                    token_count = self.text_processor.estimate_tokens(chunk_content)

                    chunk = DocumentChunk(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        content=chunk_content,
                        embedding=embedding,
                        token_count=token_count,
                        metadata={
                            "chunk_type": "text",
                            "batch_index": i // batch_size,
                            "content_length": len(chunk_content),
                        },
                    )

                    db.add(chunk)

                # Flush after each batch to avoid memory issues
                await db.flush()
                logger.debug(f"Processed batch {i // batch_size + 1} of chunks")

            except Exception as e:
                logger.error(
                    f"Error processing chunk batch {i}-{i + len(batch_chunks)}: {e}"
                )
                raise DocumentIngestionError(f"Failed to process chunk batch: {str(e)}")

    async def get_document_status(
        self, db: AsyncSession, document_id: str
    ) -> Optional[Document]:
        """Get document by ID with chunk count."""
        try:
            stmt = select(Document).where(Document.id == document_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
