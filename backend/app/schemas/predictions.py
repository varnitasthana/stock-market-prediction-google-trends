from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PredictionBase(BaseModel):
    model_run_id: int
    symbol: str
    prediction_date: date


class PredictionRequest(BaseModel):
    model_run_id: int = Field(..., gt=0)
    symbol: str = Field(..., min_length=1, max_length=50)
    prediction_date: date


class PredictionResponse(PredictionBase):
    id: int
    predicted_return: Decimal | None = None
    predicted_direction: int | None = None
    probability: Decimal | None = None
    actual_return: Decimal | None = None
    actual_direction: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassificationPredictionResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    symbol: str
    prediction_date: date
    target_name: str
    predicted_class: int
    predicted_direction: str
    probability_down: float | None = None
    probability_up: float | None = None
    shap_values: list[float] | None = None
    feature_columns: list[str] | None = None


class RegressionPredictionResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    symbol: str
    prediction_date: date
    target_name: str
    predicted_return: float
    shap_values: list[float] | None = None
    feature_columns: list[str] | None = None
