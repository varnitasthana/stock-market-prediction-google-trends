from pydantic import BaseModel
from datetime import date
from typing import Optional


class TrendsDataResponse(BaseModel):
    id: int
    search_term_id: int
    date: date
    interest_score: Optional[int] = None

    model_config = {"from_attributes": True}
