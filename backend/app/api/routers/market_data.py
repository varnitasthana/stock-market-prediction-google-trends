from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.pipeline.market_pipeline import MarketIngestionService
from app.schemas.market_data import (
    LiveQuoteResponse,
    MarketCoverage,
    MarketDataIngestRequest,
    MarketDataIngestResponse,
    MarketDataResponse,
    MarketDataStatusResponse,
    MarketRefreshRequest,
    MarketRefreshResponse,
)
from app.services.market_data_service import MarketDataService

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=list[MarketDataResponse])
async def get_market_data(
    symbol: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = MarketDataService(db)
    return await service.get_market_data(symbol, start_date, end_date)


@router.get("/symbols")
async def list_symbols(db: AsyncSession = Depends(get_db)):
    """Symbols present in the database, with their stored coverage.

    ``supported`` lists the symbols this deployment is configured to track so
    the UI can offer them even before any data has been downloaded.
    """
    service = MarketDataService(db)
    return {
        "supported": settings.supported_symbols,
        "default": settings.default_market_symbol,
        "stored": await service.list_available_symbols(),
    }


@router.get("/status/{symbol}", response_model=MarketDataStatusResponse)
async def get_market_data_status(symbol: str, db: AsyncSession = Depends(get_db)):
    """How current the stored history is, so the UI can show a freshness badge."""
    service = MarketDataService(db)
    return await service.get_status(symbol)


@router.get("/live/{symbol}", response_model=LiveQuoteResponse)
async def get_live_quote(symbol: str, db: AsyncSession = Depends(get_db)):
    """Latest stored close with its change against the previous session."""
    service = MarketDataService(db)
    return await service.get_live_quote(symbol)


@router.get("/recent/{symbol}", response_model=list[MarketDataResponse])
async def get_recent_market_data(symbol: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = MarketDataService(db)
    return await service.get_recent(symbol, limit)


@router.post("/refresh", response_model=MarketRefreshResponse)
async def refresh_market_data(request: MarketRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Re-download recent sessions from the provider and recompute metrics.

    Overlapping rows are refreshed rather than duplicated, so this is safe to
    call repeatedly.
    """
    service = MarketDataService(db)
    return await service.refresh(request.symbol, lookback_days=request.lookback_days)


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

    coverage = result.get("coverage") or {}
    return MarketDataIngestResponse(
        symbol=result["symbol"],
        total_records=result["total_records"],
        inserted=result["inserted"],
        updated=result.get("updated", 0),
        metrics_refreshed=result.get("metrics_refreshed", 0),
        date_range=result["date_range"],
        coverage=MarketCoverage(
            row_count=coverage.get("row_count", 0),
            first_date=coverage.get("first_date"),
            last_date=coverage.get("last_date"),
        ),
    )
