import logging
from pathlib import Path

import pandas as pd

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def save_parquet(df: pd.DataFrame, filename: str) -> Path:
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"{filename}.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Saved {len(df)} rows to {path}")
    return path


def load_parquet(filename: str) -> pd.DataFrame:
    path = Path("data/processed") / f"{filename}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_parquet(path)
