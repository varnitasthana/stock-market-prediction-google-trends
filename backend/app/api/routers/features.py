from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.services.feature_service import FeatureService

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
