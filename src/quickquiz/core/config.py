"""Configuration management for QuickQuiz-GPT."""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./quickquiz.db"
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_password: str = ""
    redis_db: int = 0

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-ada-002"
    openai_max_retries: int = 3
    openai_timeout: int = 60

    # Application
    app_name: str = "QuickQuiz-GPT"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    max_request_size: int = 52428800  # 50MB

    # File Upload Settings
    max_file_size_mb: int = 50
    allowed_file_types: list[str] = ["application/pdf"]
    upload_temp_dir: str = "/tmp"

    # Text Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    batch_size: int = 10

    # URL Extraction
    url_timeout: int = 30
    url_max_retries: int = 3
    url_user_agent: str = "QuickQuiz-GPT/1.0"

    # Embedding Service
    embedding_dimension: int = 1536
    embedding_batch_size: int = 50

    # Caching
    cache_ttl_documents: int = 86400  # 1 day
    cache_ttl_embeddings: int = 604800  # 1 week
    cache_ttl_questions: int = 3600  # 1 hour

    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_requests_per_hour: int = 1000

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"


settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
