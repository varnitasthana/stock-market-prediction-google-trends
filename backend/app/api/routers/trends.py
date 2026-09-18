from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
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
