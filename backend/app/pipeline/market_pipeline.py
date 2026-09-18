import logging
from datetime import date
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.models.database import MarketData
from app.repositories.market_data_repo import MarketDataRepository
from app.utils.validators import validate_ohlcv

logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def fetch_market_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
    if df.empty:
        raise MarketDataError(f"No data returned for {symbol}")
    df = df.reset_index()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["symbol"] = symbol
    df = df.rename(columns={"stock splits": "stock_splits"})
    return df


class MarketIngestionService:
    def __init__(self, db):
        self.repo = MarketDataRepository(db)

    async def ingest(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        logger.info(f"Starting market data ingestion for {symbol}")
        df = fetch_market_data(symbol, start_date, end_date)
        df = validate_ohlcv(df)

        existing = await self.repo.get_by_symbol_and_date_range(symbol, date.fromisoformat(start_date), date.fromisoformat(end_date))
        existing_dates = {r.date for r in existing}
        new_records = []
        for _, row in df.iterrows():
            if row["date"] not in existing_dates:
                new_records.append({
                    "symbol": row["symbol"],
                    "date": row["date"],
                    "open": float(row["open"]) if pd.notna(row["open"]) else None,
                    "high": float(row["high"]) if pd.notna(row["high"]) else None,
                    "low": float(row["low"]) if pd.notna(row["low"]) else None,
                    "close": float(row["close"]) if pd.notna(row["close"]) else None,
                    "adj_close": float(row["close"]) if pd.notna(row["close"]) else None,
                    "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                })

        if new_records:
            await self.repo.bulk_insert(new_records)
            logger.info(f"Inserted {len(new_records)} new market records for {symbol}")
        else:
            logger.info(f"No new records to insert for {symbol}")

        return {
            "symbol": symbol,
            "total_records": len(df),
            "inserted": len(new_records),
            "date_range": f"{start_date} to {end_date}",
        }
