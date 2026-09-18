from pydantic import BaseModel
from datetime import date
from typing import Optional
from decimal import Decimal


class PredictionBase(BaseModel):
    model_run_id: int
    symbol: str
    prediction_date: date


class PredictionResponse(PredictionBase):
    id: int
    predicted_return: Optional[Decimal] = None
    predicted_direction: Optional[int] = None
    probability: Optional[Decimal] = None
    actual_return: Optional[Decimal] = None
    actual_direction: Optional[int] = None
    created_at: date

    model_config = {"from_attributes": True}
