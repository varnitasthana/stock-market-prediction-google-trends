from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List, Dict, Any


class TrendsDataResponse(BaseModel):
    id: int
    search_term_id: int
    date: date
    interest_score: Optional[int] = None

    model_config = {"from_attributes": True}


class TrendsIngestRequest(BaseModel):
    search_term_id: int = Field(..., gt=0)
    start_date: date
    end_date: date


class TermIngestResult(BaseModel):
    term: str
    total_records: int = 0
    inserted: int = 0
    duplicates_skipped: int = 0
    error: Optional[str] = None


class TrendsIngestResponse(BaseModel):
    requested_term_ids: List[int]
    results: List[TermIngestResult]
    total_inserted: int = 0
    total_duplicates_skipped: int = 0
