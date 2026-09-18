import logging
from typing import Dict, Any
import pandas as pd
from app.ml.feature_engineer import FeatureEngineer
from app.repositories.features_repo import FeaturesRepository

logger = logging.getLogger(__name__)


class FeaturePipeline:
    def __init__(self, db):
        self.db = db
        self.repo = FeaturesRepository(db)

    async def run(self, symbol: str, start_date: str, end_date: str, trends_data: pd.DataFrame | None = None) -> Dict[str, Any]:
        from app.repositories.market_data_repo import MarketDataRepository
        market_repo = MarketDataRepository(self.db)

        from datetime import date
        market_records = await market_repo.get_by_symbol_and_date_range(
            symbol, date.fromisoformat(start_date), date.fromisoformat(end_date)
        )
        if not market_records:
            raise ValueError(f"No market data found for {symbol} in the given date range")

        market_df = pd.DataFrame([
            {
                "date": r.date,
                "symbol": r.symbol,
                "open": float(r.open) if r.open else None,
                "high": float(r.high) if r.high else None,
                "low": float(r.low) if r.low else None,
                "close": float(r.close) if r.close else None,
                "volume": int(r.volume) if r.volume else None,
            }
            for r in market_records
        ])

        engineer = FeatureEngineer(market_df=market_df, trends_df=trends_data)
        feature_df = engineer.get_feature_dataframe()

        records = []
        for _, row in feature_df.iterrows():
            for col in feature_df.columns:
                if col in ["date", "symbol", "target_direction", "next_day_return", "open", "high", "low", "close", "adj_close", "volume"]:
                    continue
                val = row.get(col)
                if pd.isna(val):
                    continue
                records.append({
                    "symbol": symbol,
                    "date": row["date"],
                    "feature_name": col,
                    "feature_value": float(val),
                })

        if records:
            await self.repo.bulk_insert(records)
            logger.info(f"Inserted {len(records)} feature records for {symbol}")

        return {"symbol": symbol, "total_features": len(records), "samples": len(feature_df)}
