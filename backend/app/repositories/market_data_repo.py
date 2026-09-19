from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MarketData


class MarketDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_symbol_and_date_range(self, symbol: str, start_date, end_date):
        stmt = (
            select(MarketData)
            .where(MarketData.symbol == symbol)
            .where(MarketData.date >= start_date)
            .where(MarketData.date <= end_date)
            .order_by(MarketData.date)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest_date(self, symbol: str):
        stmt = (
            select(MarketData.date)
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.date.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_insert(self, records: list[dict]):
        if not records:
            return
        stmt = insert(MarketData).values(records)
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_by_symbol(self, symbol: str, limit: int = 100):
        stmt = (
            select(MarketData)
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
