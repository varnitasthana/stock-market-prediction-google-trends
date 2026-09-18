from pydantic import BaseModel
from datetime import date
from typing import Optional
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
