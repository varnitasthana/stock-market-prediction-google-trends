import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_ohlcv(df: "pd.DataFrame") -> "pd.DataFrame":
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
