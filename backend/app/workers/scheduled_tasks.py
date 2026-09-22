import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


def select_market_ingestion_window(
    latest: date | None,
    settings,
    reference=None,
) -> tuple[date, date] | None:
    """Select a settled-session window without requesting future data."""
    from app.utils import trading_calendar

    end_date = trading_calendar.latest_expected_session(reference)
    if latest is not None and latest >= end_date:
        return None

    start_date = (
        trading_calendar.next_business_day(latest)
        if latest is not None
        else settings.resolved_start_date(end_date)
    )
    if start_date > end_date:
        return None
    return start_date, end_date


async def _get_db_session():
    from app.core.database import get_db
    async for session in get_db():
        yield session


def daily_market_ingestion() -> dict[str, Any]:
    from app.pipeline.market_pipeline import MarketIngestionService
    from app.services.market_data_service import MarketDataService
    import asyncio

    async def run():
        async for db in _get_db_session():
            service = MarketIngestionService(db)
            market_service = MarketDataService(db)
            latest = await market_service.get_latest_date("^NSEI")
            end_date = date.today()
            if latest:
                from datetime import timedelta
                start_date = latest + timedelta(days=1)
            else:
                from app.core.config import get_settings
                start_date = date.fromisoformat(get_settings().default_start_date)
            if start_date >= end_date:
                return {"status": "skipped", "reason": "already up to date"}
            result = await service.ingest("^NSEI", start_date.isoformat(), end_date.isoformat())
            return {"status": "success", "result": result}

    return asyncio.run(run())


def daily_trends_ingestion() -> dict[str, Any]:
    from app.pipeline.trends_pipeline import TrendsIngestionService
    from app.pipeline.trends_provider import PytrendsProvider
    from app.services.search_term_service import SearchTermService
    import asyncio

    async def run():
        async for db in _get_db_session():
            term_service = SearchTermService(db)
            terms = await term_service.list_terms(active_only=True)
            if not terms:
                return {"status": "skipped", "reason": "no active search terms"}
            provider = PytrendsProvider()
            trends_service = TrendsIngestionService(db, provider=provider)
            end_date = date.today().isoformat()
            start_date = (date.today() - __import__("datetime").timedelta(days=7)).isoformat()
            results = await trends_service.ingest_all_terms(start_date, end_date)
            return {"status": "success", "results": results}

    return asyncio.run(run())


def daily_sentiment_ingestion() -> dict[str, Any]:
    from app.services.sentiment_service import SentimentService
    import asyncio

    async def run():
        async for db in _get_db_session():
            service = SentimentService(db)
            result = await service.ingest_daily_sentiment()
            return result

    return asyncio.run(run())


def daily_feature_generation() -> dict[str, Any]:
    from app.services.feature_engineering_service import FeatureEngineer
    from app.repositories.search_term_repo import SearchTermRepository
    import asyncio

    async def run():
        async for db in _get_db_session():
            term_repo = SearchTermRepository(db)
            terms = await term_repo.get_all(active_only=False)
            term_ids = [t.id for t in terms]
            if not term_ids:
                return {"status": "skipped", "reason": "no search terms"}
            engineer = FeatureEngineer(db)
            end_date = date.today().isoformat()
            start_date = (date.today() - __import__("datetime").timedelta(days=30)).isoformat()
            result = await engineer.generate_features(
                "^NSEI",
                term_ids,
                date.fromisoformat(start_date),
                date.fromisoformat(end_date),
                persist=True,
            )
            return {"status": "success", "result": result}

    return asyncio.run(run())
