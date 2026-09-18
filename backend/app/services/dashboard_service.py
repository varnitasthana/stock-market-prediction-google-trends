from typing import Dict, Any, List
from datetime import date


class DashboardService:
    def __init__(self, db):
        self.db = db

    async def get_summary(self, symbol: str) -> Dict[str, Any]:
        from app.repositories.market_data_repo import MarketDataRepository
        from app.repositories.prediction_repo import PredictionRepository
        from app.repositories.model_repo import ModelRepository

        market_repo = MarketDataRepository(self.db)
        prediction_repo = PredictionRepository(self.db)
        model_repo = ModelRepository(self.db)

        recent_market = await market_repo.get_by_symbol(symbol, limit=1)
        latest_market = recent_market[0] if recent_market else None

        models = await model_repo.get_all(symbol=symbol)
        latest_model = models[0] if models else None

        latest_predictions = await prediction_repo.get_latest(symbol, limit=1)
        latest_prediction = latest_predictions[0] if latest_predictions else None

        return {
            "symbol": symbol,
            "latest_close": float(latest_market.close) if latest_market and latest_market.close else None,
            "latest_date": latest_market.date.isoformat() if latest_market else None,
            "latest_daily_return": float(latest_market.daily_return) if latest_market and latest_market.daily_return else None,
            "latest_model": latest_model.model_name if latest_model else None,
            "last_training_date": latest_model.created_at.isoformat() if latest_model else None,
            "prediction_direction": latest_prediction.predicted_direction if latest_prediction else None,
            "prediction_probability": float(latest_prediction.probability) if latest_prediction and latest_prediction.probability else None,
            "prediction_date": latest_prediction.prediction_date.isoformat() if latest_prediction else None,
        }
