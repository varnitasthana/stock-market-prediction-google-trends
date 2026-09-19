import asyncio
import logging

from app.core.config import get_settings
from app.core.database import get_db, init_db
from app.pipeline.feature_pipeline import FeaturePipeline
from app.pipeline.market_pipeline import MarketIngestionService
from app.pipeline.trends_pipeline import TrendsIngestionService
from app.pipeline.trends_provider import PytrendsProvider

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_pipeline():
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.info("Initializing database...")
    await init_db()

    start_date = settings.default_start_date
    end_date = settings.default_end_date
    symbol = settings.default_market_symbol

    async for db in get_db():
        logger.info("=" * 60)
        logger.info("PHASE 1: Market Data Ingestion")
        logger.info("=" * 60)
        market_service = MarketIngestionService(db)
        try:
            market_result = await market_service.ingest(symbol, start_date, end_date)
            logger.info(f"Market ingestion complete: {market_result}")
        except Exception as e:
            logger.error(f"Market ingestion failed: {e}")

        logger.info("=" * 60)
        logger.info("PHASE 2: Google Trends Ingestion")
        logger.info("=" * 60)
        trends_provider = PytrendsProvider(sleep_seconds=settings.pytrends_sleep)
        trends_service = TrendsIngestionService(db, provider=trends_provider)
        try:
            trends_results = await trends_service.ingest_all_terms(start_date, end_date)
            for result in trends_results:
                logger.info(f"Trends result: {result}")
        except Exception as e:
            logger.error(f"Trends ingestion failed: {e}")

        logger.info("=" * 60)
        logger.info("PHASE 3: Feature Engineering")
        logger.info("=" * 60)
        feature_pipeline = FeaturePipeline(db)
        try:
            feature_result = await feature_pipeline.run(symbol, start_date, end_date)
            logger.info(f"Feature engineering complete: {feature_result}")
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")

        logger.info("=" * 60)
        logger.info("Pipeline complete")
        logger.info("=" * 60)
        break


if __name__ == "__main__":
    asyncio.run(run_pipeline())
