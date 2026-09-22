import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.repositories.market_data_repo import MarketDataRepository
from app.utils.market_metrics import (
    VOLATILITY_WINDOW,
    attach_market_metrics,
    clean_metric,
)
from app.utils.validators import validate_ohlcv

logger = logging.getLogger(__name__)

#: yfinance treats ``end`` as *exclusive*, so we add a day to include the
#: requested end date in the downloaded window.
_END_DATE_PADDING = timedelta(days=1)

OHLCV_COLUMNS = ("open", "high", "low", "close", "adj_close", "volume")


class MarketDataError(Exception):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def fetch_market_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Download daily OHLCV history for ``symbol`` from Yahoo Finance.

    ``end_date`` is inclusive in this API (yfinance's exclusive ``end`` is
    padded internally).
    """
    inclusive_end = (date.fromisoformat(end_date) + _END_DATE_PADDING).isoformat()
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=inclusive_end, auto_adjust=True)

    if df.empty:
        raise MarketDataError(
            f"No data returned for {symbol} between {start_date} and {end_date}"
        )

    df = df.reset_index()
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

    if "date" not in df.columns:
        raise MarketDataError(f"Downloaded data for {symbol} has no date column")

    # ``index`` is renamed to ``date`` for some yfinance versions.
    if "index" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"index": "date"})

    df["date"] = pd.to_datetime(df["date"]).dt.date
    # yfinance timestamps carry a timezone; normalise to a plain calendar date.
    if "adj_close" not in df.columns and "close" in df.columns:
        df["adj_close"] = df["close"]
    df["symbol"] = symbol

    return df


class MarketIngestionService:
    def __init__(self, db):
        self.repo = MarketDataRepository(db)

    async def ingest(self, symbol: str, start_date: str, end_date: str) -> dict[str, Any]:
        """Download ``symbol`` history and store it, refreshing derived metrics."""
        logger.info("Starting market data ingestion for %s (%s -> %s)", symbol, start_date, end_date)

        df = fetch_market_data(symbol, start_date, end_date)
        df = validate_ohlcv(df)

        existing = await self.repo.get_by_symbol_and_date_range(
            symbol, date.fromisoformat(start_date), date.fromisoformat(end_date)
        )
        existing_dates = {row.date for row in existing}

        records = []
        for row in df.to_dict("records"):
            if pd.isna(row.get("close")) or row["date"] is None:
                continue
            records.append(
                {
                    "symbol": symbol,
                    "date": row["date"],
                    "open": clean_metric(row.get("open")),
                    "high": clean_metric(row.get("high")),
                    "low": clean_metric(row.get("low")),
                    "close": clean_metric(row.get("close")),
                    "adj_close": clean_metric(row.get("adj_close", row.get("close"))),
                    "volume": int(row["volume"]) if pd.notna(row.get("volume")) else None,
                }
            )

        new_rows = [record for record in records if record["date"] not in existing_dates]

        written = await self.repo.upsert(records)
        metrics_written = await self.recompute_metrics(symbol)

        logger.info(
            "Ingested %s: %s downloaded, %s new, %s written, %s metrics refreshed",
            symbol,
            len(records),
            len(new_rows),
            written,
            metrics_written,
        )

        coverage = await self.repo.get_coverage(symbol)
        return {
            "symbol": symbol,
            "total_records": len(records),
            "inserted": len(new_rows),
            "updated": written - len(new_rows),
            "metrics_refreshed": metrics_written,
            "date_range": f"{start_date} to {end_date}",
            "coverage": coverage,
        }

    async def recompute_metrics(self, symbol: str) -> int:
        """Recompute ``daily_return`` and ``volatility`` for every stored row.

        Both metrics depend on neighbouring closes, so ingesting a new row also
        fixes the previously-last row (which had no "next day" before).
        """
        series = await self.repo.get_close_series(symbol)
        if len(series) < 2:
            return 0

        frame = pd.DataFrame(
            {"date": [row[0] for row in series], "close": [clean_metric(row[1]) for row in series]}
        )
        frame = frame.dropna(subset=["close"])
        if frame.empty:
            return 0

        frame = attach_market_metrics(frame, window=VOLATILITY_WINDOW)

        metrics = {
            row["date"]: (clean_metric(row["daily_return"]), clean_metric(row["volatility"]))
            for _, row in frame.iterrows()
        }
        return await self.repo.update_metrics(symbol, metrics)
