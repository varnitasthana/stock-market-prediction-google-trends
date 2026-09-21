from pydantic import BaseModel


class FeatureImportance(BaseModel):
    feature: str
    shap_value: float


class ExplainabilityResponse(BaseModel):
    model_run_id: int
    model_name: str
    task_type: str
    prediction_date: str
    predicted_class: int | None = None
    predicted_return: float | None = None
    predicted_direction: str | None = None
    top_features: list[FeatureImportance]
    feature_importance: dict[str, float]
