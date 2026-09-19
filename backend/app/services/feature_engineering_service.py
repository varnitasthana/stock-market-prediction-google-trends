import logging
from datetime import date
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.repositories.market_data_repo import MarketDataRepository
from app.repositories.trends_repo import TrendsRepository
from app.repositories.search_term_repo import SearchTermRepository
from app.repositories.features_repo import FeaturesRepository
from app.schemas.alignment import AlignedRow
from app.utils.validators import validate_market_data, validate_trends_data

logger = logging.getLogger(__name__)


class FeatureEngineeringError(Exception):
    pass


class FeatureEngineer:
    def __init__(self, db):
        self.market_repo = MarketDataRepository(db)
        self.trends_repo = TrendsRepository(db)
        self.term_repo = SearchTermRepository(db)
        self.features_repo = FeaturesRepository(db)

    async def generate_features(
        self,
        symbol: str,
        search_term_ids: List[int],
        start_date: date,
        end_date: date,
        persist: bool = True,
    ) -> Dict[str, Any]:
        market_rows = await self.market_repo.get_by_symbol_and_date_range(symbol, start_date, end_date)
        if not market_rows:
            raise FeatureEngineeringError(f"No market data found for {symbol} in range {start_date} to {end_date}")

        market_df = self._market_to_df(market_rows)
        market_df = validate_market_data(market_df, symbol)
        market_df = market_df.sort_values("date").reset_index(drop=True)

        market_df["daily_return"] = self._calculate_returns(market_df["close"])
        market_df["log_return"] = self._calculate_log_returns(market_df["close"])
        market_df["volatility_5d"] = self._calculate_rolling_volatility(market_df["daily_return"], window=5)
        market_df["return_lag_1"] = market_df["daily_return"].shift(1)
        market_df["return_lag_3"] = market_df["daily_return"].shift(3)
        market_df["return_lag_5"] = market_df["daily_return"].shift(5)

        terms = await self.term_repo.get_all(active_only=False)
        term_map = {t.id: t.term for t in terms}

        trends_data = {}
        for term_id in search_term_ids:
            term_name = term_map.get(term_id)
            if not term_name:
                continue

            trends_rows = await self.trends_repo.get_by_term_and_date_range(term_id, start_date, end_date)
            if not trends_rows:
                continue

            trends_df = self._trends_to_df(trends_rows)
            trends_df = validate_trends_data(trends_df)
            trends_df = trends_df.sort_values("date").reset_index(drop=True)

            safe_term = self._sanitize_term(term_name)
            market_df[f"{safe_term}_trend"] = self._merge_trends_to_market(market_df["date"], trends_df)
            market_df[f"{safe_term}_trend_lag_1"] = market_df[f"{safe_term}_trend"].shift(1)
            market_df[f"{safe_term}_trend_lag_3"] = market_df[f"{safe_term}_trend"].shift(3)
            market_df[f"{safe_term}_trend_lag_7"] = market_df[f"{safe_term}_trend"].shift(7)
            market_df[f"{safe_term}_trend_change"] = market_df[f"{safe_term}_trend"].diff(1)

        market_df["next_day_return"] = market_df["daily_return"].shift(-1)
        market_df["next_day_direction"] = (market_df["next_day_return"] > 0).astype(int)

        feature_df = market_df.dropna(subset=["daily_return", "volatility_5d", "next_day_return"]).copy()
        feature_df = feature_df.sort_values("date").reset_index(drop=True)

        if feature_df.empty:
            raise FeatureEngineeringError("No valid feature rows after removing insufficient history")

        feature_df = self._validate_final_dataset(feature_df)

        records = []
        for _, row in feature_df.iterrows():
            row_date = row["date"]
            for col in feature_df.columns:
                if col in {"date", "open", "high", "low", "close", "adj_close", "volume"}:
                    continue
                value = row[col]
                if pd.isna(value) or value is None or np.isinf(value):
                    continue
                records.append({
                    "symbol": symbol,
                    "date": row_date,
                    "feature_name": col,
                    "feature_value": float(value),
                })

        if persist and records:
            await self.features_repo.bulk_insert(records)
            logger.info("Persisted %s engineered feature records for %s", len(records), symbol)

        feature_names = sorted({r["feature_name"] for r in records})
        return {
            "symbol": symbol,
            "rows_generated": len(feature_df),
            "rows_persisted": len(records),
            "features_generated": feature_names,
            "date_range": f"{start_date} to {end_date}",
        }

    @staticmethod
    def _calculate_returns(close_series: pd.Series) -> pd.Series:
        return close_series.pct_change(1)

    @staticmethod
    def _calculate_log_returns(close_series: pd.Series) -> pd.Series:
        return np.log(close_series / close_series.shift(1))

    @staticmethod
    def _calculate_rolling_volatility(returns: pd.Series, window: int = 5) -> pd.Series:
        return returns.rolling(window=window, min_periods=window).std()

    @staticmethod
    def _merge_trends_to_market(market_dates: pd.Series, trends_df: pd.DataFrame) -> pd.Series:
        trends_indexed = {row["date"]: row["interest_score"] for row in trends_df.to_dict("records")}
        return market_dates.map(trends_indexed)

    @staticmethod
    def _sanitize_term(term: str) -> str:
        return term.lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _validate_final_dataset(df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isna().any():
                logger.warning("Column %s contains NaN values", col)
            if np.isinf(df[col]).any():
                logger.warning("Column %s contains infinite values", col)
        return df

    @staticmethod
    def _market_to_df(rows: List[Any]) -> pd.DataFrame:
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
    def _trends_to_df(rows: List[Any]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=["date", "interest_score"])
        data = []
        for r in rows:
            data.append({
                "date": r.date,
                "interest_score": r.interest_score,
            })
        return pd.DataFrame(data)
