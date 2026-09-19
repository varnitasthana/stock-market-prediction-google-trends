
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import ModelRun
from app.schemas.models import ModelRunCreate


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

    async def update_artifact_path(self, model_run_id: int, artifact_path: str):
        model_run = await self.get_by_id(model_run_id)
        if not model_run:
            return None
        model_run.artifact_path = artifact_path
        await self.db.flush()
        await self.db.refresh(model_run)
        return model_run
