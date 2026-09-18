from pydantic import BaseModel
from datetime import date
from typing import Optional
from decimal import Decimal


class EngineeredFeatureResponse(BaseModel):
    id: int
    symbol: str
    date: date
    feature_name: str
    feature_value: Optional[Decimal] = None

    model_config = {"from_attributes": True}
