from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List
from app.core.database import get_db
from app.services.statistical_analysis_service import StatisticalAnalysisService, StatisticalAnalysisError
from app.schemas.statistics import StatisticsAnalyzeRequest, StatisticsAnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=StatisticsAnalyzeResponse)
async def analyze_statistics(request: StatisticsAnalyzeRequest, db: AsyncSession = Depends(get_db)):
    service = StatisticalAnalysisService(db)
    try:
        result = await service.analyze(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
        )
    except StatisticalAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Statistical analysis failed: {exc}") from exc

    return StatisticsAnalyzeResponse(
        symbol=result["symbol"],
        date_range=result["date_range"],
        sample_size=result["sample_size"],
        descriptive_statistics=result["descriptive_statistics"],
        correlations=result["correlations"],
        lag_analysis=result["lag_analysis"],
        direction_analysis=result["direction_analysis"],
    )
