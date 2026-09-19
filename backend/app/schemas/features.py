from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from decimal import Decimal


class EngineeredFeatureResponse(BaseModel):
    id: int
    symbol: str
    date: date
    feature_name: str
    feature_value: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class FeatureGenerateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    search_term_ids: List[int] = Field(default_factory=list, min_length=1)
    start_date: date
    end_date: date


class FeatureGenerateResponse(BaseModel):
    symbol: str
    rows_generated: int = 0
    rows_persisted: int = 0
    features_generated: List[str] = []
