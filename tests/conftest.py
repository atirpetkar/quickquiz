"""Test configuration and fixtures for QuickQuiz-GPT."""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.quickquiz.core.database import Base
from src.quickquiz.core.config import Settings


# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class TestSettings(Settings):
    """Test-specific settings."""
    database_url: str = TEST_DATABASE_URL
    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = "test-key"
    debug: bool = True


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return TestSettings()


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Test Document",
        "source_type": "text", 
        "content": "This is a sample document content for testing purposes. It contains educational material about machine learning algorithms.",
        "metadata": {"test": True}
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "question_text": "What is machine learning?",
        "question_type": "multiple_choice",
        "options": [
            {"label": "A", "text": "A type of artificial intelligence"},
            {"label": "B", "text": "A programming language"},
            {"label": "C", "text": "A database system"},
            {"label": "D", "text": "A web framework"}
        ],
        "correct_answer": "A",
        "explanation": "Machine learning is a subset of artificial intelligence.",
        "difficulty_level": "medium",
        "bloom_level": "Understanding"
    }
