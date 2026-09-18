from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.services.market_data_service import MarketDataService
from app.schemas.market_data import MarketDataResponse

router = APIRouter()


@router.get("/", response_model=list[MarketDataResponse])
async def get_market_data(
    symbol: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = MarketDataService(db)
    return await service.get_market_data(symbol, start_date, end_date)


@router.get("/recent/{symbol}", response_model=list[MarketDataResponse])
async def get_recent_market_data(symbol: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = MarketDataService(db)
    return await service.get_recent(symbol, limit)
