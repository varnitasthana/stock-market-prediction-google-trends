from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from decimal import Decimal


class MarketDataBase(BaseModel):
    symbol: str
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adj_close: Optional[Decimal] = None
    volume: Optional[int] = None


class MarketDataResponse(MarketDataBase):
    id: int
    daily_return: Optional[Decimal] = None
    volatility: Optional[Decimal] = None

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
