from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.schemas.alignment import AlignmentRequest, AlignmentResponse
from app.services.alignment_service import AlignmentService

router = APIRouter()


@router.post("/", response_model=AlignmentResponse)
async def align_data(request: AlignmentRequest, db: AsyncSession = Depends(get_db)):
    service = AlignmentService(db)
    try:
        result = await service.align(
            symbol=request.symbol,
            search_term_id=request.search_term_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Alignment failed: {exc}") from exc

    return AlignmentResponse(
        symbol=request.symbol,
        search_term_id=request.search_term_id,
        rows=result["rows"],
        quality=result["quality"],
    )
