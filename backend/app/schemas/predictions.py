from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PredictionBase(BaseModel):
    model_run_id: int
    symbol: str
    prediction_date: date


class PredictionResponse(PredictionBase):
    id: int
    predicted_return: Decimal | None = None
    predicted_direction: int | None = None
    probability: Decimal | None = None
    actual_return: Decimal | None = None
    actual_direction: int | None = None
    created_at: date

    model_config = {"from_attributes": True}
