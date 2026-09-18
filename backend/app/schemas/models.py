from pydantic import BaseModel
from datetime import date
from typing import Optional, Any, Dict


class ModelRunBase(BaseModel):
    model_name: str
    symbol: str
    training_start: date
    training_end: date
    evaluation_start: date
    evaluation_end: date


class ModelRunCreate(ModelRunBase):
    pass


class ModelRunResponse(ModelRunBase):
    id: int
    metrics: Optional[Dict[str, Any]] = None
    created_at: date

    model_config = {"from_attributes": True}
