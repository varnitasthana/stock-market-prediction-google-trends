import logging
from datetime import date
from typing import Any

import pandas as pd

from app.repositories.market_data_repo import MarketDataRepository
from app.repositories.search_term_repo import SearchTermRepository
from app.repositories.trends_repo import TrendsRepository
from app.schemas.alignment import AlignedRow, DataQualityReport
from app.utils.validators import validate_market_data, validate_trends_data

logger = logging.getLogger(__name__)


class AlignmentService:
    def __init__(self, db):
        self.market_repo = MarketDataRepository(db)
        self.trends_repo = TrendsRepository(db)
        self.term_repo = SearchTermRepository(db)

    async def align(self, symbol: str, search_term_id: int, start_date: date, end_date: date) -> dict[str, Any]:
        market_rows = await self.market_repo.get_by_symbol_and_date_range(symbol, start_date, end_date)
        trends_rows = await self.trends_repo.get_by_term_and_date_range(search_term_id, start_date, end_date)

        market_df = self._market_to_df(market_rows)
        trends_df = self._trends_to_df(trends_rows)

        market_df = validate_market_data(market_df, symbol)
        trends_df = validate_trends_data(trends_df)

        duplicate_market_rows = int(len(market_rows) - len(market_df))
        duplicate_trends_rows = int(len(trends_rows) - len(trends_df))

        market_dates = set(market_df["date"]) if not market_df.empty else set()
        trends_dates = set(trends_df["date"]) if not trends_df.empty else set()

        overlapping_dates = sorted(market_dates & trends_dates)
        unmatched_market_dates = sorted(market_dates - trends_dates)
        unmatched_trends_dates = sorted(trends_dates - market_dates)

        market_indexed = {row["date"]: row for row in market_df.to_dict("records")}
        trends_indexed = {row["date"]: row for row in trends_df.to_dict("records")}

        aligned_rows: list[AlignedRow] = []
        for d in overlapping_dates:
            m = market_indexed[d]
            t = trends_indexed[d]
            aligned_rows.append(AlignedRow(
                date=d,
                symbol=symbol,
                close=float(m["close"]) if pd.notna(m.get("close")) else None,
                open=float(m["open"]) if pd.notna(m.get("open")) else None,
                high=float(m["high"]) if pd.notna(m.get("high")) else None,
                low=float(m["low"]) if pd.notna(m.get("low")) else None,
                volume=int(m["volume"]) if pd.notna(m.get("volume")) else None,
                interest_score=int(t["interest_score"]) if pd.notna(t.get("interest_score")) else None,
                search_term_id=search_term_id,
            ))

        quality = DataQualityReport(
            market_rows=len(market_rows),
            trends_rows=len(trends_rows),
            valid_market_rows=len(market_df),
            valid_trends_rows=len(trends_df),
            duplicate_market_rows=duplicate_market_rows,
            duplicate_trends_rows=duplicate_trends_rows,
            aligned_rows=len(aligned_rows),
            unmatched_market_dates=unmatched_market_dates,
            unmatched_trends_dates=unmatched_trends_dates,
            date_range_start=start_date,
            date_range_end=end_date,
        )

        logger.info(
            "Aligned %s rows for symbol=%s term=%s range=%s to %s",
            len(aligned_rows),
            symbol,
            search_term_id,
            start_date,
            end_date,
        )

        return {"rows": aligned_rows, "quality": quality}

    @staticmethod
    def _market_to_df(rows: list[Any]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])
        data = []
        for r in rows:
            data.append({
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "adj_close": r.adj_close,
                "volume": r.volume,
            })
        return pd.DataFrame(data)

    @staticmethod
    def _trends_to_df(rows: list[Any]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=["date", "interest_score"])
        data = []
        for r in rows:
            data.append({
                "date": r.date,
                "interest_score": r.interest_score,
            })
        return pd.DataFrame(data)
