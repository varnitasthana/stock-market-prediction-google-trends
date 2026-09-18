from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.models.database import ModelRun
from app.schemas.models import ModelRunCreate
from datetime import date


class ModelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, symbol: str | None = None):
        stmt = select(ModelRun)
        if symbol:
            stmt = stmt.where(ModelRun.symbol == symbol)
        stmt = stmt.order_by(ModelRun.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, model_run_id: int):
        stmt = select(ModelRun).where(ModelRun.id == model_run_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, model_data: ModelRunCreate):
        model_run = ModelRun(**model_data.model_dump())
        self.db.add(model_run)
        await self.db.flush()
        await self.db.refresh(model_run)
        return model_run
