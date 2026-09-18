from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(symbol: str = Query(...), db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_summary(symbol)
