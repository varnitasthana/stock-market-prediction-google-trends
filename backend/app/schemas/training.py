from datetime import date
from typing import Any

from pydantic import BaseModel, Field

SUPPORTED_CLASSIFICATION_MODELS = {"logistic_regression", "random_forest_classifier", "lstm_classifier", "transformer_classifier"}
SUPPORTED_REGRESSION_MODELS = {"linear_regression", "random_forest_regressor", "lstm_regressor", "transformer_regressor"}
SUPPORTED_TASKS = {"classification", "regression"}


class ModelTrainRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date
    task: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)


class ModelTrainResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    symbol: str
    target_name: str
    feature_names: list[str]
    feature_count: int
    parameters: dict[str, Any]
    random_state: int
    training_rows: int
    validation_rows: int
    test_rows: int
    training_start_date: str | None = None
    training_end_date: str | None = None
    validation_start_date: str | None = None
    validation_end_date: str | None = None
    test_start_date: str | None = None
    test_end_date: str | None = None
    training_completed: bool
    train_prediction_shape: list[int]
    validation_prediction_shape: list[int]
    test_prediction_shape: list[int]
    artifact_path: str | None = None
