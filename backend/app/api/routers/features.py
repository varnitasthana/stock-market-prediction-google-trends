from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List
from app.core.database import get_db
from app.services.feature_service import FeatureService
from app.services.feature_engineering_service import FeatureEngineer, FeatureEngineeringError
from app.schemas.features import EngineeredFeatureResponse, FeatureGenerateRequest, FeatureGenerateResponse

router = APIRouter()


@router.get("/")
async def get_features(
    symbol: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    data = await service.get_features(symbol, start_date, end_date)
    return [
        {"id": f.id, "symbol": f.symbol, "date": f.date.isoformat(), "feature_name": f.feature_name, "feature_value": float(f.feature_value) if f.feature_value else None}
        for f in data
    ]


@router.post("/generate", response_model=FeatureGenerateResponse)
async def generate_features(request: FeatureGenerateRequest, db: AsyncSession = Depends(get_db)):
    engineer = FeatureEngineer(db)
    try:
        result = await engineer.generate_features(
            symbol=request.symbol,
            search_term_ids=request.search_term_ids,
            start_date=request.start_date,
            end_date=request.end_date,
            persist=True,
        )
    except FeatureEngineeringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Feature generation failed: {exc}") from exc

    return FeatureGenerateResponse(
        symbol=result["symbol"],
        rows_generated=result["rows_generated"],
        rows_persisted=result["rows_persisted"],
        features_generated=result["features_generated"],
    )
