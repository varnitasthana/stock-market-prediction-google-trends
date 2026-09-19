from datetime import date

from pydantic import BaseModel, Field


class MLDatasetPrepareRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date
    train_ratio: float = Field(default=0.70, ge=0.0, le=1.0)
    validation_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    test_ratio: float = Field(default=0.15, ge=0.0, le=1.0)


class MLDatasetPrepareResponse(BaseModel):
    symbol: str
    start_date: date
    end_date: date
    original_rows: int
    rows_after_cleaning: int
    rows_removed: int
    feature_count: int
    feature_names: list[str]
    target_names: list[str]
    train_rows: int
    validation_rows: int
    test_rows: int
    train_start_date: str | None = None
    train_end_date: str | None = None
    validation_start_date: str | None = None
    validation_end_date: str | None = None
    test_start_date: str | None = None
    test_end_date: str | None = None
    train_ratio: float
    validation_ratio: float
    test_ratio: float
    leakage_safe: bool
    quality_issues: list[str] = []
    X_train_shape: list[int]
    X_validation_shape: list[int]
    X_test_shape: list[int]
