from datetime import date

from pydantic import BaseModel


class PredictionRequest(BaseModel):
    model_run_id: int
    symbol: str
    prediction_date: date


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


class RegressionPredictionResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    symbol: str
    prediction_date: date
    target_name: str
    predicted_return: float
