from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MarketDataBase(BaseModel):
    symbol: str
    date: date
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    adj_close: Decimal | None = None
    volume: int | None = None


class MarketDataResponse(MarketDataBase):
    id: int
    daily_return: Decimal | None = None
    volatility: Decimal | None = None

    model_config = {"from_attributes": True}


class MarketDataIngestRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date


class MarketDataIngestResponse(BaseModel):
    symbol: str
    total_records: int = 0
    inserted: int = 0
    updated: int = 0
    metrics_refreshed: int = 0
    date_range: str = ""
    coverage: "MarketCoverage | None" = None


class MarketCoverage(BaseModel):
    """How much history is actually stored for a symbol."""

    row_count: int = 0
    first_date: date | None = None
    last_date: date | None = None


class MarketDataStatusResponse(BaseModel):
    """Data-freshness snapshot used by the UI to show a live/stale badge."""

    symbol: str
    today: date
    expected_session: date
    last_stored_date: date | None = None
    sessions_behind: int = 0
    is_stale: bool = False
    calendar_days_behind: int | None = None
    row_count: int = 0
    first_stored_date: date | None = None
    has_derived_metrics: bool = False
    last_checked_at: datetime
    message: str = ""


class LiveQuoteResponse(BaseModel):
    """Latest price plus the change against the previous stored session."""

    symbol: str
    as_of: date | None = None
    price: float | None = None
    previous_close: float | None = None
    change: float | None = None
    change_percent: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    day_open: float | None = None
    volume: int | None = None
    direction: str = "flat"
    source: str = "database"
    is_live: bool = False
    retrieved_at: datetime


class MarketRefreshRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    lookback_days: int = Field(
        30,
        ge=1,
        le=3650,
        description="How far back to re-download. Overlapping rows are refreshed, not duplicated.",
    )


class MarketRefreshResponse(BaseModel):
    symbol: str
    requested_start: date
    requested_end: date
    downloaded_rows: int = 0
    new_rows: int = 0
    updated_rows: int = 0
    metrics_refreshed: int = 0
    latest_stored_date: date | None = None
    status: MarketDataStatusResponse | None = None
    message: str = ""


MarketDataIngestResponse.model_rebuild()
