from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.models.database import Prediction
from app.schemas.predictions import PredictionBase


class PredictionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_model_run(self, model_run_id: int):
        stmt = (
            select(Prediction)
            .where(Prediction.model_run_id == model_run_id)
            .order_by(Prediction.prediction_date.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest(self, symbol: str, limit: int = 10):
        stmt = (
            select(Prediction)
            .where(Prediction.symbol == symbol)
            .order_by(Prediction.prediction_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def bulk_insert(self, records: list[dict]):
        if not records:
            return
        stmt = insert(Prediction).values(records)
        await self.db.execute(stmt)
        await self.db.flush()
