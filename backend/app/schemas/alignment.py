from datetime import date

from pydantic import BaseModel


class DataQualityReport(BaseModel):
    market_rows: int = 0
    trends_rows: int = 0
    valid_market_rows: int = 0
    valid_trends_rows: int = 0
    duplicate_market_rows: int = 0
    duplicate_trends_rows: int = 0
    aligned_rows: int = 0
    unmatched_market_dates: list[date] = []
    unmatched_trends_dates: list[date] = []
    date_range_start: date | None = None
    date_range_end: date | None = None


class AlignedRow(BaseModel):
    date: date
    symbol: str
    close: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: int | None = None
    interest_score: int | None = None
    search_term_id: int | None = None


class AlignmentRequest(BaseModel):
    symbol: str
    search_term_id: int
    start_date: date
    end_date: date


class AlignmentResponse(BaseModel):
    symbol: str
    search_term_id: int
    rows: list[AlignedRow]
    quality: DataQualityReport
