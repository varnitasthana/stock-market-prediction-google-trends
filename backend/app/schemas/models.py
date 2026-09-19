from datetime import date
from typing import Any

from pydantic import BaseModel


class ModelRunBase(BaseModel):
    model_name: str
    symbol: str
    task_type: str = "classification"
    target_name: str = "next_day_direction"
    training_start: date
    training_end: date
    evaluation_start: date
    evaluation_end: date
    test_start_date: date | None = None
    test_end_date: date | None = None


class ModelRunCreate(ModelRunBase):
    pass


class ModelRunResponse(ModelRunBase):
    id: int
    task_type: str | None = None
    target_name: str | None = None
    test_start_date: date | None = None
    test_end_date: date | None = None
    parameters: dict[str, Any] | None = None
    random_state: int | None = None
    feature_count: int | None = None
    artifact_path: str | None = None
    metrics: dict[str, Any] | None = None
    created_at: date

    model_config = {"from_attributes": True}
