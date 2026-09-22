from datetime import date, timedelta
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings

from app.utils import trading_calendar


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
    # ``None`` or empty means "today". Resolved at request time so the default
    # window can never silently rot the way a hard-coded date does.
    default_end_date: str | None = None
    default_lookback_days: int = 365
    #: Missed sessions before the dataset is flagged as stale in the UI.
    stale_session_threshold: int = 1
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

    # --- Derived windows -----------------------------------------------------
    # Every default range is anchored to the current date rather than a literal
    # string baked into the source.

    def resolved_end_date(self) -> date:
        """End of the default data window: configured date, otherwise today."""
        if self.default_end_date:
            return date.fromisoformat(self.default_end_date)
        return trading_calendar.today()

    def resolved_start_date(self, end: date | None = None) -> date:
        """Start of the default data window."""
        if self.default_start_date:
            return date.fromisoformat(self.default_start_date)
        anchor = end or self.resolved_end_date()
        return anchor - timedelta(days=self.default_lookback_days)

    def default_window(self) -> tuple[date, date]:
        """The default ``(start, end)`` range, always ending on a live date."""
        end = self.resolved_end_date()
        return self.resolved_start_date(end), end


@lru_cache
def get_settings() -> Settings:
    return Settings()
