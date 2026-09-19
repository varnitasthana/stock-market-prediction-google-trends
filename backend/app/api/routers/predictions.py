from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.get("/")
async def get_predictions(symbol: str | None = None, model_run_id: int | None = None, db: AsyncSession = Depends(get_db)):
    service = PredictionService(db)
    if model_run_id:
        return await service.get_predictions_by_model_run(model_run_id)
    if symbol:
        return await service.get_latest_predictions(symbol)
    raise HTTPException(status_code=400, detail="Provide symbol or model_run_id")
