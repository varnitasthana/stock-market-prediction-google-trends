from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
from app.models.database import SearchTerm
from app.schemas.search_terms import SearchTermCreate, SearchTermUpdate


class SearchTermRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True):
        stmt = select(SearchTerm)
        if active_only:
            stmt = stmt.where(SearchTerm.active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, term_id: int):
        stmt = select(SearchTerm).where(SearchTerm.id == term_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_term(self, term: str):
        stmt = select(SearchTerm).where(SearchTerm.term == term)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, term_data: SearchTermCreate):
        search_term = SearchTerm(**term_data.model_dump())
        self.db.add(search_term)
        await self.db.flush()
        await self.db.refresh(search_term)
        return search_term

    async def update(self, term_id: int, update_data: SearchTermUpdate):
        stmt = update(SearchTerm).where(SearchTerm.id == term_id).values(**update_data.model_dump(exclude_none=True))
        await self.db.execute(stmt)
        await self.db.flush()
        return await self.get_by_id(term_id)

    async def delete(self, term_id: int):
        stmt = delete(SearchTerm).where(SearchTerm.id == term_id)
        await self.db.execute(stmt)
        await self.db.flush()
