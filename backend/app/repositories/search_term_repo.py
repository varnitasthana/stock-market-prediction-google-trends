from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import SearchTerm, TrendsData
from app.schemas.search_terms import SearchTermCreate, SearchTermUpdate


class SearchTermRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True):
        stmt = select(SearchTerm)
        if active_only:
            stmt = stmt.where(SearchTerm.active)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_trend_coverage(self) -> dict[int, dict]:
        """``{search_term_id: {row_count, first_date, last_date}}``.

        One grouped query, so listing terms stays cheap regardless of how many
        trend rows exist.
        """
        stmt = (
            select(
                TrendsData.search_term_id,
                func.count(TrendsData.id),
                func.min(TrendsData.date),
                func.max(TrendsData.date),
            )
            .group_by(TrendsData.search_term_id)
        )
        rows = (await self.db.execute(stmt)).all()
        return {
            term_id: {
                "row_count": int(count or 0),
                "first_date": first_date,
                "last_date": last_date,
            }
            for term_id, count, first_date, last_date in rows
        }

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
