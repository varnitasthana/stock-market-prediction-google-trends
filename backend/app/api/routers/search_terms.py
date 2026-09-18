from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.search_term_service import SearchTermService
from app.schemas.search_terms import SearchTermCreate, SearchTermUpdate, SearchTermResponse

router = APIRouter()


@router.get("/", response_model=list[SearchTermResponse])
async def list_search_terms(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    service = SearchTermService(db)
    return await service.list_terms(active_only=active_only)


@router.post("/", response_model=SearchTermResponse, status_code=201)
async def create_search_term(term_data: SearchTermCreate, db: AsyncSession = Depends(get_db)):
    service = SearchTermService(db)
    return await service.create_term(term_data)


@router.get("/{term_id}", response_model=SearchTermResponse)
async def get_search_term(term_id: int, db: AsyncSession = Depends(get_db)):
    service = SearchTermService(db)
    return await service.get_term(term_id)


@router.put("/{term_id}", response_model=SearchTermResponse)
async def update_search_term(term_id: int, update_data: SearchTermUpdate, db: AsyncSession = Depends(get_db)):
    service = SearchTermService(db)
    return await service.update_term(term_id, update_data)


@router.delete("/{term_id}")
async def delete_search_term(term_id: int, db: AsyncSession = Depends(get_db)):
    service = SearchTermService(db)
    return await service.delete_term(term_id)
