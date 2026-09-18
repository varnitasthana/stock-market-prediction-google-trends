"""
Development seed script for Phase 5 manual testing.

This script inserts deterministic sample market data and trends data
into the development database so you can manually verify the alignment API.

It is NOT production data. It is for local testing only.
"""
import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models.database import MarketData, TrendsData, SearchTerm
from app.repositories.search_term_repo import SearchTermRepository

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/stock_prediction"

SAMPLE_MARKET = [
    {"symbol": "ALIGN", "date": date(2024, 1, 1), "close": 100.0, "volume": 1000},
    {"symbol": "ALIGN", "date": date(2024, 1, 2), "close": 101.0, "volume": 1100},
    {"symbol": "ALIGN", "date": date(2024, 1, 3), "close": 102.0, "volume": 1200},
    {"symbol": "ALIGN", "date": date(2024, 1, 4), "close": 103.0, "volume": 1300},
    {"symbol": "ALIGN", "date": date(2024, 1, 5), "close": 104.0, "volume": 1400},
]

SAMPLE_TRENDS = [
    {"search_term_id": 1, "date": date(2024, 1, 1), "interest_score": 10},
    {"search_term_id": 1, "date": date(2024, 1, 2), "interest_score": 20},
    {"search_term_id": 1, "date": date(2024, 1, 4), "interest_score": 40},
    {"search_term_id": 1, "date": date(2024, 1, 5), "interest_score": 50},
]


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        term_repo = SearchTermRepository(session)
        term = await term_repo.get_by_term("recession")
        if not term:
            term = await term_repo.create({"term": "recession", "category": "macro", "active": True})
            print(f"Created search term id={term.id}")
        else:
            print(f"Using existing search term id={term.id}")

        for row in SAMPLE_MARKET:
            session.add(MarketData(**row))
        try:
            await session.flush()
            await session.commit()
            print(f"Inserted {len(SAMPLE_MARKET)} market rows")
        except Exception as exc:
            if "UniqueViolation" in str(exc) or "duplicate key" in str(exc).lower():
                print("Market data already exists, skipping insert")
                await session.rollback()
            else:
                raise

        for row in SAMPLE_TRENDS:
            row["search_term_id"] = term.id
            session.add(TrendsData(**row))
        try:
            await session.flush()
            await session.commit()
            print(f"Inserted {len(SAMPLE_TRENDS)} trends rows")
        except Exception as exc:
            if "UniqueViolation" in str(exc) or "duplicate key" in str(exc).lower():
                print("Trends data already exists, skipping insert")
                await session.rollback()
            else:
                raise

    await engine.dispose()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
