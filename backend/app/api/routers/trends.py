import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.pipeline.trends_pipeline import TrendsIngestionService
from app.pipeline.trends_provider import PytrendsProvider
from app.schemas.trends import (
    TermIngestResult,
    TrendsIngestRequest,
    TrendsIngestResponse,
)
from app.services.trends_service import TrendsService

logger = logging.getLogger(__name__)

router = APIRouter()


class TrendsRefreshRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


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


@router.post("/refresh", response_model=TrendsIngestResponse)
async def refresh_all_trends(request: TrendsRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh Google Trends data for all active search terms."""
    from app.repositories.search_term_repo import SearchTermRepository

    settings = get_settings()
    end_date = request.end_date or settings.resolved_end_date()
    start_date = request.start_date or settings.resolved_start_date(end_date)

    term_repo = SearchTermRepository(db)
    terms = await term_repo.get_all(active_only=True)
    if not terms:
        raise HTTPException(status_code=404, detail="No active search terms found")

    provider = PytrendsProvider()
    ingestion_service = TrendsIngestionService(db, provider)

    results = []
    total_inserted = 0
    total_duplicates = 0

    for term in terms:
        try:
            result = await ingestion_service.ingest_term(
                term=term.term,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
            results.append(TermIngestResult(**result))
            total_inserted += result.get("inserted", 0)
            total_duplicates += result.get("total_records", 0) - result.get("inserted", 0)
        except Exception as exc:
            logger.error(f"Failed to refresh trends for {term.term}: {exc}")
            results.append(TermIngestResult(term=term.term, error=str(exc)))

    return TrendsIngestResponse(
        requested_term_ids=[t.id for t in terms],
        results=results,
        total_inserted=total_inserted,
        total_duplicates_skipped=total_duplicates,
    )
