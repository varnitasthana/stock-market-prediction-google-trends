from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Stock Market Prediction System"
    api_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-must-be-at-least-32-chars-long"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_prediction"
    pytrends_retries: int = 3
    pytrends_sleep: int = 1
    default_market_symbol: str = "^NSEI"
    default_start_date: str = "2024-01-01"
    default_end_date: str = "2026-09-21"
    mlflow_tracking_uri: str | None = None
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    sentiment_api_key: str | None = None
    supported_symbols: list[str] = ["^NSEI", "^NSEBANK", "^CNXIT"]
    
    # Security settings
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    rate_limit_per_minute: int = 60
    max_request_size: int = 10485760  # 10MB

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("api_env") == "production" and v == "change-me-in-production":
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
