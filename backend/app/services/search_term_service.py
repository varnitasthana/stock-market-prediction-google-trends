from fastapi import HTTPException

from app.repositories.search_term_repo import SearchTermRepository
from app.schemas.search_terms import (
    SearchTermCreate,
    SearchTermUpdate,
)


class SearchTermService:
    def __init__(self, db):
        self.repo = SearchTermRepository(db)

    async def list_terms(self, active_only: bool = True):
        return await self.repo.get_all(active_only=active_only)

    async def list_terms_with_coverage(
        self, active_only: bool = True, with_data_only: bool = False
    ) -> list[dict]:
        """Terms plus their stored trend coverage, sorted by name.

        ``with_data_only`` hides placeholder terms that have no trend rows, so
        the UI cannot chart a term that would render an empty series.
        """
        terms = await self.repo.get_all(active_only=active_only)
        coverage = await self.repo.get_trend_coverage()

        result = []
        for term in terms:
            stats = coverage.get(
                term.id, {"row_count": 0, "first_date": None, "last_date": None}
            )
            has_trends = stats["row_count"] > 0
            if with_data_only and not has_trends:
                continue
            result.append(
                {
                    "id": term.id,
                    "term": term.term,
                    "category": term.category,
                    "active": term.active,
                    "created_at": term.created_at,
                    "trend_row_count": stats["row_count"],
                    "trend_first_date": stats["first_date"],
                    "trend_last_date": stats["last_date"],
                    "has_trends": has_trends,
                }
            )

        result.sort(key=lambda row: row["term"])
        return result

    async def get_term(self, term_id: int):
        term = await self.repo.get_by_id(term_id)
        if not term:
            raise HTTPException(status_code=404, detail="Search term not found")
        return term

    async def create_term(self, term_data: SearchTermCreate):
        existing = await self.repo.get_by_term(term_data.term)
        if existing:
            raise HTTPException(status_code=409, detail="Search term already exists")
        return await self.repo.create(term_data)

    async def update_term(self, term_id: int, update_data: SearchTermUpdate):
        term = await self.repo.get_by_id(term_id)
        if not term:
            raise HTTPException(status_code=404, detail="Search term not found")

        if update_data.term and update_data.term != term.term:
            existing = await self.repo.get_by_term(update_data.term)
            if existing and existing.id != term_id:
                raise HTTPException(status_code=409, detail="Search term already exists")

        return await self.repo.update(term_id, update_data)

    async def delete_term(self, term_id: int):
        term = await self.repo.get_by_id(term_id)
        if not term:
            raise HTTPException(status_code=404, detail="Search term not found")
        await self.repo.delete(term_id)
        return {"message": "Search term deleted"}
