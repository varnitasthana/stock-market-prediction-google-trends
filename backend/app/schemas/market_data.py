from datetime import date
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
    date_range: str = ""
