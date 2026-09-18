import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Stock Market Prediction System"
    api_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_prediction"
    pytrends_retries: int = 3
    pytrends_sleep: int = 1
    default_market_symbol: str = "NSEI"
    default_start_date: str = "2018-01-01"
    default_end_date: str = "2025-01-01"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
