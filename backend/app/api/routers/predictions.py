from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.predictions import ClassificationPredictionResponse, RegressionPredictionResponse, PredictionRequest
from app.services.prediction_service import PredictionError, PredictionService

router = APIRouter()


@router.get("/")
async def get_predictions(symbol: str | None = None, model_run_id: int | None = None, db: AsyncSession = Depends(get_db)):
    service = PredictionService(db, model_run_id=0, symbol=symbol or "", prediction_date=None)
    if model_run_id:
        return await service.get_predictions_by_model_run(model_run_id)
    if symbol:
        return await service.get_latest_predictions(symbol)
    raise HTTPException(status_code=400, detail="Provide symbol or model_run_id")


@router.post("/", response_model=ClassificationPredictionResponse | RegressionPredictionResponse)
async def predict(request: PredictionRequest, db: AsyncSession = Depends(get_db)):
    service = PredictionService(db, model_run_id=request.model_run_id, symbol=request.symbol, prediction_date=request.prediction_date)
    try:
        result = await service.predict()
    except PredictionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    if result["task_type"] == "classification":
        return ClassificationPredictionResponse(**result)
    return RegressionPredictionResponse(**result)
