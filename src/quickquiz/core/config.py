"""Configuration management for QuickQuiz-GPT."""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql://user:password@localhost/quickquiz"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # OpenAI
    openai_api_key: str = ""

    # Application
    app_name: str = "QuickQuiz-GPT"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
