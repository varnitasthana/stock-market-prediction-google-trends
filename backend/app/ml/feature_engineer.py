import logging
from datetime import date
from typing import Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngineer:
    def __init__(self, market_df: pd.DataFrame, trends_df: pd.DataFrame | None = None):
        self.market_df = market_df.copy()
        self.trends_df = trends_df.copy() if trends_df is not None else None
        self.features: Dict[str, pd.Series] = {}

    def create_market_features(self) -> pd.DataFrame:
        df = self.market_df.copy()
        df = df.sort_values("date").reset_index(drop=True)

        df["daily_return"] = df["close"].pct_change()
        df["volume_change"] = df["volume"].pct_change()

        df["return_5d"] = df["close"].pct_change(5)
        df["return_10d"] = df["close"].pct_change(10)
        df["return_20d"] = df["close"].pct_change(20)

        df["ma_5"] = df["close"].rolling(window=5).mean()
        df["ma_10"] = df["close"].rolling(window=10).mean()
        df["ma_20"] = df["close"].rolling(window=20).mean()

        df["ma_distance_5"] = (df["close"] - df["ma_5"]) / df["ma_5"]
        df["ma_distance_10"] = (df["close"] - df["ma_10"]) / df["ma_10"]

        df["momentum_5"] = df["close"] - df["close"].shift(5)
        df["momentum_10"] = df["close"] - df["close"].shift(10)

        df["volatility_5d"] = df["daily_return"].rolling(window=5).std()
        df["volatility_10d"] = df["daily_return"].rolling(window=10).std()
        df["volatility_20d"] = df["daily_return"].rolling(window=20).std()

        self.market_df = df
        return df

    def create_trend_features(self, term: str, interest_col: str = "interest_score") -> pd.DataFrame:
        if self.trends_df is None or interest_col not in self.trends_df.columns:
            return pd.DataFrame()

        df = self.trends_df.copy()
        df = df.sort_values("date").reset_index(drop=True)

        df["interest_lag_1"] = df[interest_col].shift(1)
        df["interest_lag_3"] = df[interest_col].shift(3)
        df["interest_lag_5"] = df[interest_col].shift(5)
        df["interest_lag_7"] = df[interest_col].shift(7)

        df["interest_change_1d"] = df[interest_col].diff(1)
        df["interest_change_3d"] = df[interest_col].diff(3)
        df["interest_change_7d"] = df[interest_col].diff(7)

        df["interest_pct_change"] = df[interest_col].pct_change()

        df["interest_ma_3"] = df[interest_col].rolling(window=3).mean()
        df["interest_ma_7"] = df[interest_col].rolling(window=7).mean()

        df["interest_std_3"] = df[interest_col].rolling(window=3).std()
        df["interest_std_7"] = df[interest_col].rolling(window=7).std()

        df["interest_momentum"] = df[interest_col] - df[interest_col].shift(3)

        feature_cols = [c for c in df.columns if c.startswith("interest") or c == "date"]
        return df[feature_cols]

    def create_target(self) -> pd.DataFrame:
        df = self.market_df.copy()
        df["next_day_return"] = df["close"].shift(-1) / df["close"] - 1
        df["target_direction"] = (df["next_day_return"] > 0).astype(int)
        return df

    def get_feature_dataframe(self) -> pd.DataFrame:
        market_features = self.create_market_features()
        target_df = self.create_target()

        result = target_df.copy()

        if self.trends_df is not None:
            for term in self.trends_df["term"].unique() if "term" in self.trends_df.columns else [None]:
                if term is None:
                    continue
                term_df = self.trends_df[self.trends_df["term"] == term].copy()
                term_features = self.create_trend_features(term)
                if not term_features.empty:
                    term_features = term_features.rename(
                        columns={c: f"{c}_{term}" for c in term_features.columns if c != "date"}
                    )
                    result = result.merge(term_features, on="date", how="left")

        result = result.dropna(subset=["target_direction", "next_day_return"])
        return result
