import logging
from datetime import date
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import pandas as pd

from app.utils.validators import validate_trends_data

logger = logging.getLogger(__name__)

try:
    import urllib3

    if not hasattr(urllib3.Retry, "__patched_for_pytrends__"):
        original_init = urllib3.Retry.__init__

        def _patched_init(self, *args, **kwargs):
            if "method_whitelist" in kwargs:
                kwargs["allowed_methods"] = kwargs.pop("method_whitelist")
            return original_init(self, *args, **kwargs)

        urllib3.Retry.__init__ = _patched_init
        urllib3.Retry.__patched_for_pytrends__ = True
except Exception:
    pass


class TrendsDataProvider(ABC):
    @abstractmethod
    async def fetch_term(self, term: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError


class PytrendsProvider(TrendsDataProvider):
    def __init__(self, sleep_seconds: float = 1.0):
        self.sleep_seconds = sleep_seconds

    def _fetch_blocking(self, term: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            from pytrends.request import TrendReq
        except ImportError as exc:
            raise RuntimeError("pytrends is not installed") from exc

        pytrends = TrendReq(retries=3, backoff_factor=1)
        pytrends.build_payload([term], timeframe=f"{start_date} {end_date}")
        df = pytrends.interest_over_time()
        if df.empty or term not in df.columns:
            raise ValueError(f"No trends data returned for {term}")

        df = df.reset_index()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.rename(columns={term: "interest_score"})
        return validate_trends_data(df)

    async def fetch_term(self, term: str, start_date: str, end_date: str) -> pd.DataFrame:
        import asyncio

        logger.info("Fetching Google Trends for term: %s", term)
        await asyncio.sleep(self.sleep_seconds)
        try:
            return await asyncio.to_thread(self._fetch_blocking, term, start_date, end_date)
        except Exception as exc:
            logger.error("Trends provider failed for %s: %s", term, exc)
            raise
