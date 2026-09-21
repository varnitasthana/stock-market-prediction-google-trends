from typing import Any

from pydantic import BaseModel, Field


class SentimentResponse(BaseModel):
    symbol: str
    date: str
    sentiment_score: float
    sentiment_label: str
    source: str
    details: dict[str, Any] | None = None


class SentimentTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class SentimentTextResponse(BaseModel):
    score: float
    label: str
    positive_count: int
    negative_count: int
