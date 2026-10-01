"""Bootstrap a fresh database into a demo-ready state.

Run once after migrating. Safe to re-run: every step is idempotent and only
fills gaps, so an existing database is left intact.

    python scripts/bootstrap_demo.py

What it does, in order:

1. Ensures the schema exists (``alembic upgrade head``).
2. Seeds the active search terms used for Google Trends features.
3. Ingests real market history for the default symbol from yfinance.
4. Pulls real Google Trends interest-over-time data for each term.
5. Generates engineered features for the aligned window.

External network calls (steps 3-4) are skipped by default when the data is
already present, so re-running is cheap. Pass ``--force`` to re-pull anyway.
"""

import argparse
import asyncio
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.database import (
    EngineeredFeature,
    MarketData,
    SearchTerm,
    TrendsData,
)
from app.pipeline.market_pipeline import MarketIngestionService
from app.pipeline.trends_pipeline import TrendsIngestionService
from app.pipeline.trends_provider import PytrendsProvider
from app.repositories.search_term_repo import SearchTermRepository
from app.services.feature_engineering_service import FeatureEngineer
from app.utils import trading_calendar

BACKEND_ROOT = Path(__file__).resolve().parent.parent

#: Terms the feature pipeline and dashboard expect to exist.
DEFAULT_TERMS = [
    ("stock market", "finance"),
    ("nifty 50", "indices"),
    ("sensex", "indices"),
    ("share price", "finance"),
    ("mutual funds", "investment"),
    ("inflation", "economy"),
    ("interest rates", "economy"),
    ("recession", "economy"),
    ("unemployment", "economy"),
    ("budget 2026", "policy"),
]

def log(msg: str = "") -> None:
    print(msg, flush=True)


def _log_step(step: int, total: int, title: str) -> None:
    log()
    log("=" * 68)
    log(f"  Step {step}/{total}: {title}")
    log("=" * 68)


def run_migrations() -> None:
    """Apply Alembic migrations so the schema matches the ORM models."""
    log("Applying database migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log("Migration failed:")
        log(result.stdout)
        log(result.stderr)
        raise SystemExit(1)
    log("Schema is up to date.")


async def seed_search_terms(session: AsyncSession) -> list[SearchTerm]:
    """Create the default terms, skipping any that already exist."""
    repo = SearchTermRepository(session)
    created = 0
    for term, category in DEFAULT_TERMS:
        existing = await repo.get_by_term(term)
        if existing:
            continue
        from app.schemas.search_terms import SearchTermCreate

        await repo.create(SearchTermCreate(term=term, category=category, active=True))
        created += 1
    await session.commit()

    terms = await repo.get_all(active_only=True)
    log(f"Search terms ready: {len(terms)} active ({created} newly created).")
    return terms


async def count_rows(session: AsyncSession, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar()


async def ingest_market_data(session: AsyncSession, symbol: str, start: date, end: date, force: bool) -> None:
    rows = (
        await session.execute(
            select(func.count(), func.min(MarketData.date), func.max(MarketData.date))
            .where(MarketData.symbol == symbol)
        )
    ).one()

    if rows[0] > 0 and not force:
        log(f"Market data already present: {rows[0]} rows, {rows[1]} to {rows[2]}. Skipping (use --force to re-pull).")
        return

    log(f"Fetching {symbol} market history from yfinance...")
    try:
        result = await MarketIngestionService(session).ingest(symbol, start.isoformat(), end.isoformat())
    except Exception as exc:
        log(f"WARNING: market ingestion failed: {exc}")
        log("The dashboard will show no market data until this succeeds.")
        return

    log(
        f"Market data: {result['inserted']} new rows "
        f"({result['metrics_refreshed']} derived metrics refreshed) "
        f"for {result['date_range']}."
    )
    # The pipeline repositories only flush; the FastAPI dependency owns the
    # commit. This script uses a bare session, so it must commit explicitly or
    # the work is discarded when the session closes.
    await session.commit()


async def ingest_trends_data(
    session: AsyncSession, terms: list[SearchTerm], start: date, end: date, force: bool
) -> None:
    rows = await count_rows(session, TrendsData)
    if rows > 0 and not force:
        log(f"Trends data already present: {rows} rows. Skipping (use --force to re-pull).")
        return

    log(f"Pulling Google Trends for {len(terms)} terms from {start} to {end}...")
    log("This hits Google's public endpoint and is rate limited; it can take a minute.")

    service = TrendsIngestionService(session, PytrendsProvider())
    results = await service.ingest_all_terms(start.isoformat(), end.isoformat())

    failed = 0
    for result in results:
        if result.get("error"):
            failed += 1
            log(f"  FAILED {result['term']}: {result['error']}")
        else:
            log(f"  {result['term']}: {result['inserted']} new / {result['total_records']} fetched")

    if failed:
        log(f"{failed} term(s) failed. Google rate-limits aggressively; re-running usually succeeds.")
        log("Retry with: python scripts/bootstrap_demo.py --force")

    await session.commit()


async def generate_features(
    session: AsyncSession, symbol: str, terms: list[SearchTerm], start: date, end: date, force: bool
) -> None:
    rows = await count_rows(session, EngineeredFeature)
    if rows > 0 and not force:
        log(f"Engineered features already present: {rows} rows. Skipping (use --force to regenerate).")
        return

    if not terms:
        log("No search terms available; skipping feature generation.")
        return

    log(f"Generating engineered features for {symbol}...")
    try:
        result = await FeatureEngineer(session).generate_features(
            symbol=symbol,
            search_term_ids=[t.id for t in terms],
            start_date=start,
            end_date=end,
            persist=True,
        )
    except Exception as exc:
        log(f"WARNING: feature generation failed: {exc}")
        log("Statistics and model pages need features; re-run once market and trends data exist.")
        return

    log(
        f"Features: {result.get('rows_persisted', 0)} values across "
        f"{len(result.get('features_generated', []))} distinct names "
        f"({result.get('rows_generated', 0)} rows, {result.get('date_range', 'n/a')})."
    )
    await session.commit()


async def summarize(session: AsyncSession) -> None:
    log()
    log("=" * 68)
    log("  Database summary")
    log("=" * 68)

    for model, name in [
        (SearchTerm, "search_terms"),
        (MarketData, "market_data"),
        (TrendsData, "trends_data"),
        (EngineeredFeature, "engineered_features"),
    ]:
        log(f"  {name:<22} {await count_rows(session, model)}")

    coverage = (
        await session.execute(
            select(MarketData.symbol, func.count(), func.min(MarketData.date), func.max(MarketData.date))
            .group_by(MarketData.symbol)
        )
    ).all()
    for symbol, count, first, last in coverage:
        log(f"  {symbol:<22} {count} rows, {first} to {last}")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a demo-ready database.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-pull data even if rows already exist.",
    )
    parser.add_argument(
        "--skip-trends",
        action="store_true",
        help="Skip Google Trends ingestion (useful when rate limited).",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Override the ingestion start date (default: DEFAULT_START_DATE).",
    )
    args = parser.parse_args()

    settings = get_settings()
    symbol = settings.default_market_symbol
    # Google Trends lags the market by 1-2 days, so stop at the last session
    # whose close is actually published rather than requesting today.
    end = trading_calendar.latest_expected_session()
    start = (
        date.fromisoformat(args.start)
        if args.start
        else settings.resolved_start_date(end)
    )

    total_steps = 4 if args.skip_trends else 5
    log("=" * 68)
    log("  BOOTSTRAPPING DEMO DATABASE")
    log("=" * 68)
    log(f"  Symbol:   {symbol}")
    log(f"  Window:   {start} to {end}")
    log(f"  Database: {_redact(settings.database_url)}")

    run_migrations()

    url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url, pool_pre_ping=True)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with maker() as session:
            _log_step(1, total_steps, "Seed search terms")
            terms = await seed_search_terms(session)

            _log_step(2, total_steps, "Ingest market data")
            await ingest_market_data(session, symbol, start, end, args.force)

            step = 3
            if not args.skip_trends:
                _log_step(step, total_steps, "Ingest Google Trends data")
                await ingest_trends_data(session, terms, start, end, args.force)
                step += 1
            else:
                log()
                log("Skipping Google Trends ingestion (--skip-trends).")

            _log_step(step, total_steps, "Generate engineered features")
            await generate_features(session, symbol, terms, start, end, args.force)

            await summarize(session)
    finally:
        await engine.dispose()

    log()
    log("=" * 68)
    log("  BOOTSTRAP COMPLETE")
    log("=" * 68)
    log("  Backend API:  http://localhost:8000/api/health")
    log("  Swagger UI:   http://localhost:8000/api/docs")
    log("  Frontend:     http://localhost:5173")
    log()
    return 0


def _redact(url: str) -> str:
    """Hide the password in a connection string before printing it."""
    if "@" not in url:
        return url
    scheme, _, rest = url.partition("://")
    credentials, _, host = rest.rpartition("@")
    if ":" in credentials:
        user, _, _ = credentials.partition(":")
        return f"{scheme}://{user}:***@{host}"
    return f"{scheme}://***@{host}"


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))