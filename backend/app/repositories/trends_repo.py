from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import TrendsData


class TrendsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_term_and_date_range(self, search_term_id: int, start_date, end_date):
        stmt = (
            select(TrendsData)
            .where(TrendsData.search_term_id == search_term_id)
            .where(TrendsData.date >= start_date)
            .where(TrendsData.date <= end_date)
            .order_by(TrendsData.date)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_term_id(self, search_term_id: int, limit: int = 100):
        stmt = (
            select(TrendsData)
            .where(TrendsData.search_term_id == search_term_id)
            .order_by(TrendsData.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def bulk_insert(self, records: list[dict]):
        if not records:
            return
        stmt = insert(TrendsData).values(records)
        await self.db.execute(stmt)
        await self.db.flush()
