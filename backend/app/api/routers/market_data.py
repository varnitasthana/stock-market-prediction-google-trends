from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.pipeline.market_pipeline import MarketIngestionService
from app.schemas.market_data import (
    MarketDataIngestRequest,
    MarketDataIngestResponse,
    MarketDataResponse,
)
from app.services.market_data_service import MarketDataService

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


@router.post("/ingest", response_model=MarketDataIngestResponse)
async def ingest_market_data(request: MarketDataIngestRequest, db: AsyncSession = Depends(get_db)):
    service = MarketIngestionService(db)
    try:
        result = await service.ingest(
            symbol=request.symbol,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data ingestion failed: {exc}") from exc

    return MarketDataIngestResponse(
        symbol=result["symbol"],
        total_records=result["total_records"],
        inserted=result["inserted"],
        date_range=result["date_range"],
    )
