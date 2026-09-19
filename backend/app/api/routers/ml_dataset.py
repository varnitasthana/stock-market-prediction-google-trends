from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List
from app.core.database import get_db
from app.services.ml_dataset_service import MLDatasetService, MLDatasetError
from app.schemas.ml_dataset import MLDatasetPrepareRequest, MLDatasetPrepareResponse

router = APIRouter()


@router.post("/prepare", response_model=MLDatasetPrepareResponse)
async def prepare_ml_dataset(request: MLDatasetPrepareRequest, db: AsyncSession = Depends(get_db)):
    total_ratio = request.train_ratio + request.validation_ratio + request.test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        raise HTTPException(status_code=400, detail=f"Split ratios must sum to 1.0, got {total_ratio}")

    service = MLDatasetService(db)
    try:
        result = await service.prepare_dataset(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            train_ratio=request.train_ratio,
            validation_ratio=request.validation_ratio,
            test_ratio=request.test_ratio,
        )
    except MLDatasetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ML dataset preparation failed: {exc}") from exc

    return MLDatasetPrepareResponse(**result)
