"""Derived market metrics shared by ingestion, refresh and repair scripts.

``daily_return`` and ``volatility`` are *derived* values. They are computed in
this single module so the numbers stored on ``market_data`` always agree with
the numbers the feature pipeline derives from ``close``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: Rolling window (in trading days) used for the stored ``volatility`` column.
#: Matches the ``volatility_5d`` engineered feature the models are trained on.
VOLATILITY_WINDOW = 5


def compute_daily_returns(close: pd.Series) -> pd.Series:
    """Simple one-period percentage change of a closing-price series."""
    return close.astype(float).pct_change(1)


def compute_rolling_volatility(
    daily_returns: pd.Series, window: int = VOLATILITY_WINDOW
) -> pd.Series:
    """Rolling standard deviation of daily returns (fractional, not annualised)."""
    return daily_returns.rolling(window=window, min_periods=window).std()


def clean_metric(value) -> float | None:
    """Coerce ``value`` to a finite float, or ``None`` when it is not usable."""
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return numeric


def attach_market_metrics(df: pd.DataFrame, window: int = VOLATILITY_WINDOW) -> pd.DataFrame:
    """Return ``df`` with ``daily_return`` and ``volatility`` recomputed.

    ``df`` must contain a ``close`` column; rows are sorted ascending by date.
    Existing values are intentionally overwritten because both metrics are a
    pure function of the close series.
    """
    out = df.sort_values("date").reset_index(drop=True).copy()
    if out.empty:
        out["daily_return"] = pd.Series(dtype="float64")
        out["volatility"] = pd.Series(dtype="float64")
        return out

    returns = compute_daily_returns(out["close"])
    out["daily_return"] = returns
    out["volatility"] = compute_rolling_volatility(returns, window=window)
    return out
