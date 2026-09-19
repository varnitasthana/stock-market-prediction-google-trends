import logging

import pandas as pd
from scipy.stats import pearsonr, spearmanr

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    def __init__(self, df: pd.DataFrame, target_col: str = "next_day_return"):
        self.df = df.copy()
        self.target_col = target_col
        self.feature_cols = [
            c for c in df.columns
            if c not in ["date", "symbol", "target_direction", "next_day_return", "close", "open", "high", "low", "adj_close", "volume"]
        ]

    def compute_pearson_correlations(self) -> pd.DataFrame:
        results = []
        target = self.df[self.target_col].dropna()
        for col in self.feature_cols:
            series = self.df[col].dropna()
            common = target.index.intersection(series.index)
            if len(common) < 10:
                continue
            try:
                corr, pval = pearsonr(target.loc[common], series.loc[common])
                results.append({"feature": col, "correlation": corr, "p_value": pval})
            except Exception as e:
                logger.warning(f"Failed to compute Pearson for {col}: {e}")
        return pd.DataFrame(results)

    def compute_spearman_correlations(self) -> pd.DataFrame:
        results = []
        target = self.df[self.target_col].dropna()
        for col in self.feature_cols:
            series = self.df[col].dropna()
            common = target.index.intersection(series.index)
            if len(common) < 10:
                continue
            try:
                corr, pval = spearmanr(target.loc[common], series.loc[common])
                results.append({"feature": col, "correlation": corr, "p_value": pval})
            except Exception as e:
                logger.warning(f"Failed to compute Spearman for {col}: {e}")
        return pd.DataFrame(results)

    def compute_lagged_correlations(self, lags: list[int]) -> pd.DataFrame:
        results = []
        target = self.df[self.target_col].dropna()
        for col in self.feature_cols:
            series = self.df[col].dropna()
            for lag in lags:
                shifted = series.shift(-lag)
                common = target.index.intersection(shifted.dropna().index)
                if len(common) < 10:
                    continue
                try:
                    corr, pval = pearsonr(target.loc[common], shifted.loc[common])
                    results.append({"feature": col, "lag": lag, "correlation": corr, "p_value": pval})
                except Exception as e:
                    logger.warning(f"Failed to compute lag {lag} for {col}: {e}")
        return pd.DataFrame(results)

    def get_top_features(self, n: int = 20, method: str = "pearson") -> pd.DataFrame:
        if method == "pearson":
            df = self.compute_pearson_correlations()
        else:
            df = self.compute_spearman_correlations()
        df = df.dropna().sort_values("correlation", key=abs, ascending=False)
        return df.head(n)
