from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import EngineeredFeature


class FeaturesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_symbol_and_date_range(self, symbol: str, start_date, end_date):
        stmt = (
            select(EngineeredFeature)
            .where(EngineeredFeature.symbol == symbol)
            .where(EngineeredFeature.date >= start_date)
            .where(EngineeredFeature.date <= end_date)
            .order_by(EngineeredFeature.date)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_symbol_and_feature(self, symbol: str, feature_name: str, limit: int = 100):
        stmt = (
            select(EngineeredFeature)
            .where(EngineeredFeature.symbol == symbol)
            .where(EngineeredFeature.feature_name == feature_name)
            .order_by(EngineeredFeature.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def bulk_insert(self, records: list[dict]):
        if not records:
            return
        stmt = pg_insert(EngineeredFeature).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=["symbol", "date", "feature_name"])
        await self.db.execute(stmt)
        await self.db.flush()
