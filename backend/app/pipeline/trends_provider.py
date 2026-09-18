import logging
from datetime import date
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import pandas as pd

from app.utils.validators import validate_trends_data

logger = logging.getLogger(__name__)


class TrendsDataProvider(ABC):
    @abstractmethod
    async def fetch_term(self, term: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError


class PytrendsProvider(TrendsDataProvider):
    def __init__(self, sleep_seconds: float = 1.0):
        self.sleep_seconds = sleep_seconds

    async def fetch_term(self, term: str, start_date: str, end_date: str) -> pd.DataFrame:
        import time
        from pytrends.request import TrendReq

        time.sleep(self.sleep_seconds)
        logger.info(f"Fetching Google Trends for term: {term}")
        pytrends = TrendReq(retries=3, backoff_factor=1)
        pytrends.build_payload([term], timeframe=f"{start_date} {end_date}")
        df = pytrends.interest_over_time()
        if df.empty or term not in df.columns:
            raise ValueError(f"No trends data returned for {term}")

        df = df.reset_index()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.rename(columns={term: "interest_score"})
        df = validate_trends_data(df)
        return df
