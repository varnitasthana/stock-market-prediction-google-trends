from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.model_service import ModelService
from app.schemas.models import ModelRunCreate, ModelRunResponse

router = APIRouter()


@router.get("/", response_model=list[ModelRunResponse])
async def list_models(symbol: str | None = None, db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    return await service.list_models(symbol=symbol)


@router.get("/{model_run_id}", response_model=ModelRunResponse)
async def get_model(model_run_id: int, db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    model = await service.get_model(model_run_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model run not found")
    return model


@router.post("/", response_model=ModelRunResponse, status_code=201)
async def create_model_run(model_data: ModelRunCreate, db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    return await service.create_model_run(model_data)
