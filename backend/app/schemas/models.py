from pydantic import BaseModel
from datetime import date
from typing import Optional, Any, Dict, List


class ModelRunBase(BaseModel):
    model_name: str
    symbol: str
    task_type: str = "classification"
    target_name: str = "next_day_direction"
    training_start: date
    training_end: date
    evaluation_start: date
    evaluation_end: date


class ModelRunCreate(ModelRunBase):
    pass


class ModelRunResponse(ModelRunBase):
    id: int
    task_type: Optional[str] = None
    target_name: Optional[str] = None
    test_start_date: Optional[date] = None
    test_end_date: Optional[date] = None
    parameters: Optional[Dict[str, Any]] = None
    random_state: Optional[int] = None
    feature_count: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    created_at: date

    model_config = {"from_attributes": True}
