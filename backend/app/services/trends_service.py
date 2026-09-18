from datetime import date
from typing import List
from app.repositories.trends_repo import TrendsRepository


class TrendsService:
    def __init__(self, db):
        self.repo = TrendsRepository(db)

    async def get_trends(self, search_term_id: int, start_date: date, end_date: date):
        return await self.repo.get_by_term_and_date_range(search_term_id, start_date, end_date)

    async def get_recent_trends(self, search_term_id: int, limit: int = 100):
        return await self.repo.get_by_term_id(search_term_id, limit=limit)
