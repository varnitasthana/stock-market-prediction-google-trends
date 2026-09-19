from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.pipeline.trends_pipeline import TrendsIngestionService
from app.pipeline.trends_provider import PytrendsProvider
from app.schemas.trends import (
    TermIngestResult,
    TrendsIngestRequest,
    TrendsIngestResponse,
)
from app.services.trends_service import TrendsService

router = APIRouter()


@router.get("/")
async def get_trends(
    search_term_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = TrendsService(db)
    data = await service.get_trends(search_term_id, start_date, end_date)
    return [
        {"id": d.id, "date": d.date.isoformat(), "interest_score": d.interest_score}
        for d in data
    ]


@router.get("/recent/{search_term_id}")
async def get_recent_trends(search_term_id: int, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = TrendsService(db)
    data = await service.get_recent_trends(search_term_id, limit)
    return [
        {"id": d.id, "date": d.date.isoformat(), "interest_score": d.interest_score}
        for d in data
    ]


@router.post("/ingest", response_model=TrendsIngestResponse)
async def ingest_trends(request: TrendsIngestRequest, db: AsyncSession = Depends(get_db)):
    from app.repositories.search_term_repo import SearchTermRepository

    search_term = await SearchTermRepository(db).get_by_id(request.search_term_id)
    if not search_term:
        raise HTTPException(status_code=404, detail="Search term not found")

    provider = PytrendsProvider()
    ingestion_service = TrendsIngestionService(db, provider)
    try:
        result = await ingestion_service.ingest_term(
            term=search_term.term,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Trends ingestion failed: {exc}") from exc

    return TrendsIngestResponse(
        requested_term_ids=[request.search_term_id],
        results=[TermIngestResult(**result)],
        total_inserted=result.get("inserted", 0),
        total_duplicates_skipped=result.get("total_records", 0) - result.get("inserted", 0),
    )
