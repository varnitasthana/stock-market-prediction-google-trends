import logging
from typing import Optional

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

    if "volume" in df.columns:
        if (df["volume"] < 0).any():
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

    return df
