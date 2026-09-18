from datetime import date
from typing import List
from app.repositories.prediction_repo import PredictionRepository


class PredictionService:
    def __init__(self, db):
        self.repo = PredictionRepository(db)

    async def get_predictions_by_model_run(self, model_run_id: int):
        return await self.repo.get_by_model_run(model_run_id)

    async def get_latest_predictions(self, symbol: str, limit: int = 10):
        return await self.repo.get_latest(symbol, limit)
