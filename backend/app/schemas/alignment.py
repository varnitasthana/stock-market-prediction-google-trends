from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class DataQualityReport(BaseModel):
    market_rows: int = 0
    trends_rows: int = 0
    valid_market_rows: int = 0
    valid_trends_rows: int = 0
    duplicate_market_rows: int = 0
    duplicate_trends_rows: int = 0
    aligned_rows: int = 0
    unmatched_market_dates: List[date] = []
    unmatched_trends_dates: List[date] = []
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None


class AlignedRow(BaseModel):
    date: date
    symbol: str
    close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    interest_score: Optional[int] = None
    search_term_id: Optional[int] = None


class AlignmentRequest(BaseModel):
    symbol: str
    search_term_id: int
    start_date: date
    end_date: date


class AlignmentResponse(BaseModel):
    symbol: str
    search_term_id: int
    rows: List[AlignedRow]
    quality: DataQualityReport
