from datetime import date

from pydantic import BaseModel, Field


class StatisticsAnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date


class DescriptiveStat(BaseModel):
    feature: str
    count: int
    mean: float
    median: float
    std: float
    min: float
    max: float


class CorrelationResult(BaseModel):
    feature: str
    target: str
    method: str
    correlation: float
    p_value: float
    sample_size: int
    adjusted_p_value: float | None = None
    significant_at_0_05: bool | None = None


class LagResult(BaseModel):
    feature: str
    target: str
    correlation: float
    p_value: float
    sample_size: int


class DirectionGroupStats(BaseModel):
    feature: str
    count: int
    mean: float
    median: float
    std: float


class StatisticsAnalyzeResponse(BaseModel):
    symbol: str
    date_range: str
    sample_size: int
    descriptive_statistics: list[DescriptiveStat] = []
    correlations: list[CorrelationResult] = []
    lag_analysis: list[LagResult] = []
    direction_analysis: dict[str, list[DirectionGroupStats]] = {}
