import logging
from datetime import date
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.repositories.features_repo import FeaturesRepository
from app.models.database import EngineeredFeature

logger = logging.getLogger(__name__)


class StatisticalAnalysisError(Exception):
    pass


class StatisticalAnalysisService:
    def __init__(self, db):
        self.features_repo = FeaturesRepository(db)

    async def analyze(self, symbol: str, start_date: date, end_date: date) -> Dict[str, Any]:
        rows = await self.features_repo.get_by_symbol_and_date_range(symbol, start_date, end_date)
        if not rows:
            raise StatisticalAnalysisError(f"No engineered features found for {symbol} in range {start_date} to {end_date}")

        wide_df = self._pivot_to_wide(rows)
        if wide_df.empty:
            raise StatisticalAnalysisError("Engineered features are empty after pivoting")

        required_targets = {"daily_return", "next_day_return", "next_day_direction"}
        missing = required_targets - set(wide_df.columns)
        if missing:
            raise StatisticalAnalysisError(f"Missing required target columns: {missing}")

        wide_df = wide_df.sort_index().reset_index(drop=True)
        n = len(wide_df)

        descriptive = self._compute_descriptive_statistics(wide_df)
        correlations = self._compute_correlations(wide_df)
        lag_analysis = self._compute_lag_analysis(wide_df)
        direction_analysis = self._compute_direction_analysis(wide_df)

        return {
            "symbol": symbol,
            "date_range": f"{start_date} to {end_date}",
            "sample_size": n,
            "descriptive_statistics": descriptive,
            "correlations": correlations,
            "lag_analysis": lag_analysis,
            "direction_analysis": direction_analysis,
        }

    @staticmethod
    def _pivot_to_wide(rows) -> pd.DataFrame:
        records = []
        for r in rows:
            records.append({
                "date": r.date,
                "feature_name": r.feature_name,
                "feature_value": float(r.feature_value) if r.feature_value is not None else np.nan,
            })
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        wide = df.pivot_table(index="date", columns="feature_name", values="feature_value", aggfunc="first")
        wide = wide.reset_index()
        wide["date"] = pd.to_datetime(wide["date"])
        wide = wide.dropna(subset=["date"])
        wide = wide.sort_values("date").reset_index(drop=True)
        return wide

    @staticmethod
    def _compute_descriptive_statistics(df: pd.DataFrame) -> List[Dict[str, Any]]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        exclude = {"next_day_direction"}
        stats_list = []
        for col in numeric_cols:
            if col in exclude:
                continue
            series = df[col].dropna()
            if series.empty:
                continue
            stats_list.append({
                "feature": col,
                "count": int(series.count()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
            })
        return stats_list

    def _compute_correlations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        trends_features = self._discover_trends_features(df.columns.tolist())
        targets = ["daily_return", "next_day_return"]
        results = []

        test_pairs = []
        for feat in trends_features:
            for target in targets:
                if feat in df.columns and target in df.columns:
                    test_pairs.append((feat, target))

        raw_pvalues = []
        for feat, target in test_pairs:
            valid = df[[feat, target]].dropna()
            if len(valid) < 3:
                continue
            x = valid[feat].values
            y = valid[target].values
            if x.std() == 0 or y.std() == 0:
                continue

            pearson_r, pearson_p = stats.pearsonr(x, y)
            spearman_r, spearman_p = stats.spearmanr(x, y)

            if np.isnan(pearson_r) or np.isnan(spearman_r):
                continue

            raw_pvalues.append(pearson_p)

            results.append({
                "feature": feat,
                "target": target,
                "method": "pearson",
                "correlation": float(pearson_r),
                "p_value": float(pearson_p),
                "sample_size": int(len(valid)),
            })
            results.append({
                "feature": feat,
                "target": target,
                "method": "spearman",
                "correlation": float(spearman_r),
                "p_value": float(spearman_p),
                "sample_size": int(len(valid)),
            })

        if raw_pvalues:
            adjusted = self._benjamini_hochberg(np.array(raw_pvalues))
            adj_idx = 0
            for res in results:
                if res["method"] == "pearson":
                    res["adjusted_p_value"] = float(adjusted[adj_idx])
                    res["significant_at_0_05"] = bool(res["adjusted_p_value"] < 0.05)
                    adj_idx += 1

        return results

    def _compute_lag_analysis(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        lag_features = [c for c in df.columns if c.endswith("_trend_lag_1") or c.endswith("_trend_lag_3") or c.endswith("_trend_lag_7")]
        results = []
        for feat in lag_features:
            if feat not in df.columns or "next_day_return" not in df.columns:
                continue
            valid = df[[feat, "next_day_return"]].dropna()
            if len(valid) < 3:
                continue
            r, p = stats.pearsonr(valid[feat].values, valid["next_day_return"].values)
            results.append({
                "feature": feat,
                "target": "next_day_return",
                "correlation": float(r),
                "p_value": float(p),
                "sample_size": int(len(valid)),
            })
        return results

    def _compute_direction_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        trends_features = self._discover_trends_features(df.columns.tolist())
        groups = {}
        for direction, group in df.groupby("next_day_direction"):
            group_stats = []
            for feat in trends_features:
                if feat not in group.columns:
                    continue
                series = group[feat].dropna()
                if series.empty:
                    continue
                group_stats.append({
                    "feature": feat,
                    "count": int(series.count()),
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "std": float(series.std()),
                })
            groups[f"direction_{int(direction)}"] = group_stats
        return groups

    @staticmethod
    def _discover_trends_features(columns: List[str]) -> List[str]:
        suffixes = ("_trend", "_trend_lag_1", "_trend_lag_3", "_trend_lag_7", "_trend_change")
        features = []
        for col in columns:
            if col in {"date", "symbol", "daily_return", "log_return", "volatility_5d",
                       "return_lag_1", "return_lag_3", "return_lag_5",
                       "next_day_return", "next_day_direction"}:
                continue
            if col.endswith(suffixes):
                features.append(col)
        return sorted(features)

    @staticmethod
    def _benjamini_hochberg(pvalues: np.ndarray) -> np.ndarray:
        n = len(pvalues)
        if n == 0:
            return np.array([])
        sorted_idx = np.argsort(pvalues)
        sorted_p = pvalues[sorted_idx]
        adjusted = np.empty(n, dtype=float)
        for i in range(n):
            adjusted[i] = sorted_p[i] * n / (i + 1)
        adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
        adjusted = np.clip(adjusted, 0.0, 1.0)
        adj_original_order = np.empty(n, dtype=float)
        adj_original_order[sorted_idx] = adjusted
        return adj_original_order
