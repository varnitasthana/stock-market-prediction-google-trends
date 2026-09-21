import logging
from datetime import date
from typing import Any

import numpy as np

from app.repositories.market_data_repo import MarketDataRepository

logger = logging.getLogger(__name__)


class SentimentError(Exception):
    pass


class SentimentService:
    def __init__(self, db):
        self.db = db
        self.market_repo = MarketDataRepository(db)

    async def ingest_daily_sentiment(self) -> dict[str, Any]:
        end_date = date.today()
        start_date = end_date
        rows = await self.market_repo.get_by_symbol_and_date_range("^NSEI", start_date, end_date)
        if not rows:
            return {"status": "skipped", "reason": "no market data for today"}
        sentiment = self._compute_market_sentiment(rows)
        return {
            "status": "success",
            "symbol": "^NSEI",
            "date": end_date.isoformat(),
            "sentiment_score": float(sentiment["score"]),
            "sentiment_label": sentiment["label"],
            "source": "derived_from_market",
        }

    def _compute_market_sentiment(self, rows: list[Any]) -> dict[str, Any]:
        if not rows:
            return {"score": 0.0, "label": "neutral"}
        latest = rows[0]
        score = 0.0
        if latest.daily_return is not None:
            score += float(latest.daily_return) * 50
        if latest.volume is not None and latest.adj_close is not None:
            avg_volume = float(latest.volume) / max(1, len(rows))
            volume_ratio = float(latest.volume) / avg_volume if avg_volume > 0 else 1.0
            score += np.clip((volume_ratio - 1.0) * 10, -20, 20)
        score = np.clip(score, -1, 1)
        if score > 0.2:
            label = "bullish"
        elif score < -0.2:
            label = "bearish"
        else:
            label = "neutral"
        return {"score": score, "label": label}

    def analyze_sentiment_text(self, text: str) -> dict[str, Any]:
        positive_words = {"up", "gain", "profit", "bullish", "positive", "growth", "rise", "surge", "rally"}
        negative_words = {"down", "loss", "bearish", "negative", "fall", "drop", "crash", "plunge", "decline"}
        words = set(text.lower().split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count
        if total == 0:
            return {"score": 0.0, "label": "neutral", "positive_count": 0, "negative_count": 0}
        score = (pos_count - neg_count) / total
        return {
            "score": float(np.clip(score, -1, 1)),
            "label": "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral",
            "positive_count": pos_count,
            "negative_count": neg_count,
        }
