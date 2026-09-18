from datetime import date
from typing import List
from app.repositories.features_repo import FeaturesRepository


class FeatureService:
    def __init__(self, db):
        self.repo = FeaturesRepository(db)

    async def get_features(self, symbol: str, start_date: date, end_date: date):
        return await self.repo.get_by_symbol_and_date_range(symbol, start_date, end_date)

    async def get_feature_by_name(self, symbol: str, feature_name: str, limit: int = 100):
        return await self.repo.get_by_symbol_and_feature(symbol, feature_name, limit)
