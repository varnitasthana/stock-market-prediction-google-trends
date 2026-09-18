from datetime import date
from typing import List, Dict, Any
from app.repositories.model_repo import ModelRepository
from app.schemas.models import ModelRunCreate, ModelRunResponse


class ModelService:
    def __init__(self, db):
        self.repo = ModelRepository(db)

    async def list_models(self, symbol: str | None = None):
        return await self.repo.get_all(symbol=symbol)

    async def get_model(self, model_run_id: int):
        return await self.repo.get_by_id(model_run_id)

    async def create_model_run(self, model_data: ModelRunCreate):
        return await self.repo.create(model_data)
