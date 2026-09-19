import logging

import pandas as pd

logger = logging.getLogger(__name__)


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=["close", "date"])
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if (df["close"] <= 0).any():
        logger.warning("Found non-positive close prices")

    if "volume" in df.columns and (df["volume"] < 0).any():
        logger.warning("Found negative volume values")

    return df


def validate_trends_data(df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in df.columns or "interest_score" not in df.columns:
        raise ValueError("Missing required columns: date, interest_score")

    df = df.dropna(subset=["date", "interest_score"])
    df = df.drop(columns=[col for col in ("isPartial",) if col in df.columns], errors="ignore")
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if (df["interest_score"] < 0).any():
        logger.warning("Found negative interest_score values")
    if (df["interest_score"] > 100).any():
        logger.warning("Found interest_score above 100")

    return df


def validate_market_data(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    required = {"date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for market data: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date

    numeric_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if "close" in df.columns and (df["close"] <= 0).any():
        logger.warning("Found non-positive close prices for %s", symbol)

    if "volume" in df.columns and (df["volume"] < 0).any():
        logger.warning("Found negative volume values for %s", symbol)

    ohlc_cols = [c for c in ("open", "high", "low", "close") if c in df.columns]
    if len(ohlc_cols) == 4:
        high = df["high"]
        low = df["low"]
        open_ = df["open"]
        close = df["close"]
        if not (high >= low).all():
            logger.warning("Found high < low for %s", symbol)
        if not (high >= open_).all():
            logger.warning("Found high < open for %s", symbol)
        if not (high >= close).all():
            logger.warning("Found high < close for %s", symbol)
        if not (low <= open_).all():
            logger.warning("Found low > open for %s", symbol)
        if not (low <= close).all():
            logger.warning("Found low > close for %s", symbol)

    return df
