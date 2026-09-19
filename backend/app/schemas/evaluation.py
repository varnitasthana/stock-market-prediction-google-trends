from pydantic import BaseModel
from typing import Any


class EvaluationRequest(BaseModel):
    model_run_id: int
    evaluation_split: str = "test"


class ConfusionMatrix(BaseModel):
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int


class ClassificationEvaluationResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    split: str
    sample_count: int
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    confusion_matrix: ConfusionMatrix | None = None
    class_distribution: dict[str, Any] | None = None
    baseline: dict[str, Any] | None = None


class RegressionEvaluationResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    split: str
    sample_count: int
    mae: float | None = None
    rmse: float | None = None
    r2: float | None = None
    baseline: dict[str, Any] | None = None
