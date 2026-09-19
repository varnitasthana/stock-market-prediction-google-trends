import logging
from datetime import date
from typing import Any

from app.pipeline.trends_provider import TrendsDataProvider
from app.repositories.search_term_repo import SearchTermRepository
from app.repositories.trends_repo import TrendsRepository
from app.schemas.search_terms import SearchTermCreate

logger = logging.getLogger(__name__)


class TrendsError(Exception):
    pass


class TrendsIngestionService:
    def __init__(self, db, provider: TrendsDataProvider):
        self.repo = SearchTermRepository(db)
        self.trends_repo = TrendsRepository(db)
        self.provider = provider

    async def ingest_term(self, term: str, start_date: str, end_date: str) -> dict[str, Any]:
        logger.info(f"Fetching Google Trends for term: {term}")
        df = await self.provider.fetch_term(term, start_date, end_date)
        if df.empty:
            raise TrendsError(f"No trends data returned for {term}")

        search_term = await self.repo.get_by_term(term)
        if not search_term:
            search_term = await self.repo.create(SearchTermCreate(term=term, category="general", active=True))

        existing = await self.trends_repo.get_by_term_and_date_range(
            search_term.id, date.fromisoformat(start_date), date.fromisoformat(end_date)
        )
        existing_dates = {r.date for r in existing}
        new_records = []
        for _, row in df.iterrows():
            if row["date"] not in existing_dates:
                new_records.append({
                    "search_term_id": search_term.id,
                    "date": row["date"],
                    "interest_score": int(row["interest_score"]),
                })

        if new_records:
            await self.trends_repo.bulk_insert(new_records)
            logger.info(f"Inserted {len(new_records)} trends records for {term}")
        else:
            logger.info(f"No new records for {term}")

        return {"term": term, "total_records": len(df), "inserted": len(new_records)}

    async def ingest_all_terms(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        terms = await self.repo.get_all(active_only=True)
        results = []
        for term in terms:
            try:
                result = await self.ingest_term(term.term, start_date, end_date)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest trends for {term.term}: {e}")
                results.append({"term": term.term, "error": str(e)})
        return results
