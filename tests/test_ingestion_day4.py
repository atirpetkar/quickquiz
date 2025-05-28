"""Tests for document ingestion functionality - Day 4."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.quickquiz.api.main import app
from src.quickquiz.core.exceptions import DocumentIngestionError
from src.quickquiz.models.schemas import DocumentCreate, SourceType
from src.quickquiz.services.embeddings import EmbeddingService
from src.quickquiz.services.ingestor import IngestionService
from src.quickquiz.utils.pdf_parser import PDFParser
from src.quickquiz.utils.text_processor import TextProcessor
from src.quickquiz.utils.url_extractor import URLExtractor

# Test client for API tests
client = TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = MagicMock(spec=EmbeddingService)
    service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    service.generate_embeddings_batch = AsyncMock(return_value=[[0.1] * 1536] * 5)
    return service


@pytest.fixture
def ingestion_service(mock_embedding_service):
    """Create ingestion service with mocked dependencies."""
    return IngestionService(mock_embedding_service)


class TestTextProcessor:
    """Test text processing functionality."""

    def test_text_processor_initialization(self):
        """Test text processor initialization."""
        processor = TextProcessor(chunk_size=500, chunk_overlap=100)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 100

    @pytest.mark.asyncio
    async def test_chunk_text_simple(self):
        """Test basic text chunking."""
        processor = TextProcessor(chunk_size=100, chunk_overlap=20)
        text = "This is a test document. " * 10

        chunks = await processor.chunk_text(text)
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)

    @pytest.mark.asyncio
    async def test_chunk_text_with_metadata(self):
        """Test text chunking with metadata."""
        processor = TextProcessor(chunk_size=100, chunk_overlap=20)
        text = "This is a test document. " * 10

        chunks_with_metadata = await processor.chunk_text_with_metadata(text)
        assert len(chunks_with_metadata) > 0

        for chunk, metadata in chunks_with_metadata:
            assert len(chunk) > 0
            assert metadata.chunk_index >= 0
            assert metadata.token_count > 0
            assert 0.0 <= metadata.quality_score <= 1.0

    def test_estimate_tokens(self):
        """Test token estimation."""
        processor = TextProcessor()
        text = "This is a simple test sentence."
        tokens = processor.estimate_tokens(text)
        assert tokens > 0
        assert tokens < len(text)  # Should be less than character count

    def test_truncate_to_tokens(self):
        """Test text truncation by tokens."""
        processor = TextProcessor()
        text = "This is a long text that should be truncated. " * 20
        truncated = processor.truncate_to_tokens(text, max_tokens=50)

        assert len(truncated) < len(text)
        assert processor.estimate_tokens(truncated) <= 50


class TestPDFParser:
    """Test PDF parsing functionality."""

    @pytest.mark.asyncio
    @patch("src.quickquiz.utils.pdf_parser.aiohttp.ClientSession.get")
    async def test_extract_from_url_success(self, mock_get):
        """Test successful PDF extraction from URL."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"mock pdf content")
        mock_get.return_value.__aenter__.return_value = mock_response

        parser = PDFParser()

        with patch.object(parser, "extract_from_bytes", return_value="Extracted text"):
            result = await parser.extract_from_url("https://example.com/test.pdf")
            assert result == "Extracted text"

    @pytest.mark.asyncio
    @patch("src.quickquiz.utils.pdf_parser.aiohttp.ClientSession.get")
    async def test_extract_from_url_http_error(self, mock_get):
        """Test PDF extraction with HTTP error."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        parser = PDFParser()

        with pytest.raises(DocumentIngestionError, match="Failed to download PDF"):
            await parser.extract_from_url("https://example.com/nonexistent.pdf")


class TestURLExtractor:
    """Test URL content extraction."""

    @pytest.mark.asyncio
    @patch("src.quickquiz.utils.url_extractor.aiohttp.ClientSession.get")
    @patch("src.quickquiz.utils.url_extractor.trafilatura.extract")
    async def test_extract_content_success(self, mock_extract, mock_get):
        """Test successful URL content extraction."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = AsyncMock(return_value="<html>Test content</html>")
        mock_get.return_value.__aenter__.return_value = mock_response

        # Mock trafilatura extraction
        mock_extract.return_value = "Extracted web content"

        async with URLExtractor() as extractor:
            result = await extractor.extract_content("https://example.com/article")
            assert "Extracted web content" in result
            assert "https://example.com/article" in result  # Should include source URL

    def test_is_valid_url(self):
        """Test URL validation."""
        extractor = URLExtractor()

        assert extractor.is_valid_url("https://example.com")
        assert extractor.is_valid_url("http://example.com/path")
        assert not extractor.is_valid_url("invalid-url")
        assert not extractor.is_valid_url("https://example.com/file.pdf")
        assert not extractor.is_valid_url("ftp://example.com")


class TestIngestionService:
    """Test document ingestion service."""

    @pytest.mark.asyncio
    async def test_ingest_text_document(self, ingestion_service, mock_db_session):
        """Test text document ingestion."""
        document_data = DocumentCreate(
            title="Test Document",
            source_type=SourceType.TEXT,
            content="This is test content for ingestion.",
        )

        # Mock database operations
        mock_document = MagicMock()
        mock_document.id = uuid.uuid4()
        mock_document.title = document_data.title
        mock_db_session.add.return_value = None

        with patch.object(
            ingestion_service, "_find_existing_document", return_value=None
        ):
            with patch.object(
                ingestion_service, "_create_chunks", return_value=["chunk1", "chunk2"]
            ):
                # Mock document creation
                with patch(
                    "src.quickquiz.models.database.Document", return_value=mock_document
                ):
                    result = await ingestion_service.ingest_document(
                        mock_db_session, document_data
                    )

                    assert mock_db_session.add.called
                    assert mock_db_session.flush.called
                    assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_ingest_duplicate_document(self, ingestion_service, mock_db_session):
        """Test ingestion of duplicate document."""
        document_data = DocumentCreate(
            title="Test Document",
            source_type=SourceType.TEXT,
            content="This is test content.",
        )

        # Mock existing document
        existing_doc = MagicMock()
        existing_doc.id = uuid.uuid4()

        with patch.object(
            ingestion_service, "_find_existing_document", return_value=existing_doc
        ):
            result = await ingestion_service.ingest_document(
                mock_db_session, document_data
            )

            assert result == existing_doc
            # Should not add new document
            assert not mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_ingest_empty_content(self, ingestion_service, mock_db_session):
        """Test ingestion with empty content."""
        document_data = DocumentCreate(
            title="Empty Document", source_type=SourceType.TEXT, content=""
        )

        with pytest.raises(DocumentIngestionError, match="too short"):
            await ingestion_service.ingest_document(mock_db_session, document_data)

    @pytest.mark.asyncio
    async def test_create_chunks(self, ingestion_service):
        """Test chunk creation."""
        content = "This is a test document with multiple sentences. " * 10
        chunks = await ingestion_service._create_chunks(content)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk.strip()) > 0 for chunk in chunks)


class TestIngestionAPI:
    """Test ingestion API endpoints."""

    @patch("src.quickquiz.api.routes.ingest.get_db")
    @patch("src.quickquiz.api.routes.ingest.get_ingestion_service")
    def test_ingest_text_endpoint(self, mock_service, mock_db):
        """Test text ingestion API endpoint."""
        # Mock dependencies
        mock_service.return_value.ingest_document = AsyncMock()
        mock_db.return_value = MagicMock()

        # Mock successful ingestion
        mock_document = MagicMock()
        mock_document.id = uuid.uuid4()
        mock_document.title = "Test Document"
        mock_document.source_type = "text"
        mock_document.source_url = None
        mock_document.content_hash = "test_hash"
        mock_document.metadata = {}
        mock_document.created_at = "2024-01-01T00:00:00"
        mock_document.updated_at = None

        mock_service.return_value.ingest_document.return_value = mock_document
        mock_service.return_value._create_chunks.return_value = ["chunk1", "chunk2"]

        response = client.post(
            "/api/v1/documents/ingest-text",
            json={
                "title": "Test Document",
                "source_type": "text",
                "content": "This is test content for the API endpoint.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["message"] == "Text content ingested successfully"

    def test_ingest_text_endpoint_missing_content(self):
        """Test text ingestion with missing content."""
        response = client.post(
            "/api/v1/documents/ingest-text",
            json={
                "title": "Test Document",
                "source_type": "text",
                # Missing content
            },
        )

        assert response.status_code == 400
        assert "Content is required" in response.json()["detail"]

    def test_ingest_text_endpoint_short_content(self):
        """Test text ingestion with too short content."""
        response = client.post(
            "/api/v1/documents/ingest-text",
            json={
                "title": "Test Document",
                "source_type": "text",
                "content": "Short",  # Too short
            },
        )

        assert response.status_code == 400
        assert "at least 50 characters" in response.json()["detail"]

    @patch("src.quickquiz.api.routes.ingest.get_db")
    def test_list_documents_endpoint(self, mock_db):
        """Test document listing endpoint."""
        # Mock database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session

        # Mock query result
        mock_result = MagicMock()
        mock_documents = [MagicMock() for _ in range(3)]
        for i, doc in enumerate(mock_documents):
            doc.id = uuid.uuid4()
            doc.title = f"Document {i}"
            doc.source_type = "text"
            doc.source_url = None
            doc.content_hash = f"hash_{i}"
            doc.metadata = {}
            doc.created_at = "2024-01-01T00:00:00"
            doc.updated_at = None

        mock_result.scalars.return_value.all.return_value = mock_documents
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/documents/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_health_check_endpoints(self):
        """Test health check endpoints."""
        # Root health check
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # API health check
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_pdf_extraction_error(self, ingestion_service, mock_db_session):
        """Test PDF extraction error handling."""
        document_data = DocumentCreate(
            title="Bad PDF",
            source_type=SourceType.PDF,
            source_url="https://example.com/bad.pdf",
        )

        with patch.object(
            ingestion_service.pdf_parser, "extract_from_url"
        ) as mock_extract:
            mock_extract.side_effect = Exception("PDF extraction failed")

            with pytest.raises(
                DocumentIngestionError, match="Failed to ingest document"
            ):
                await ingestion_service.ingest_document(mock_db_session, document_data)

            # Should rollback transaction
            assert mock_db_session.rollback.called

    @pytest.mark.asyncio
    async def test_url_extraction_error(self, ingestion_service, mock_db_session):
        """Test URL extraction error handling."""
        document_data = DocumentCreate(
            title="Bad URL",
            source_type=SourceType.URL,
            source_url="https://example.com/bad-page",
        )

        with patch(
            "src.quickquiz.utils.url_extractor.URLExtractor"
        ) as mock_extractor_class:
            mock_extractor = AsyncMock()
            mock_extractor.is_valid_url.return_value = True
            mock_extractor.extract_content.side_effect = Exception(
                "URL extraction failed"
            )
            mock_extractor_class.return_value.__aenter__.return_value = mock_extractor

            with pytest.raises(
                DocumentIngestionError, match="Failed to extract content"
            ):
                await ingestion_service.ingest_document(mock_db_session, document_data)


if __name__ == "__main__":
    pytest.main([__file__])
