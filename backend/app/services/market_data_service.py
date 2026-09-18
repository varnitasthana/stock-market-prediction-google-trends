from datetime import date
from typing import List
from app.repositories.market_data_repo import MarketDataRepository
from app.schemas.market_data import MarketDataResponse


class MarketDataService:
    def __init__(self, db):
        self.repo = MarketDataRepository(db)

    async def get_market_data(self, symbol: str, start_date: date, end_date: date):
        return await self.repo.get_by_symbol_and_date_range(symbol, start_date, end_date)

    async def get_latest_date(self, symbol: str):
        return await self.repo.get_latest_date(symbol)

    async def get_recent(self, symbol: str, limit: int = 100):
        return await self.repo.get_by_symbol(symbol, limit=limit)
