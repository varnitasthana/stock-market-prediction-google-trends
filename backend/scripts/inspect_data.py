"""One-off diagnostic: report the actual data coverage in the database."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.database import (
    EngineeredFeature,
    MarketData,
    ModelRun,
    Prediction,
    SearchTerm,
    TrendsData,
)

settings = get_settings()
URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


async def main() -> None:
    engine = create_async_engine(URL, echo=False)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        print("=== ROW COUNTS ===")
        for model, name in [
            (SearchTerm, "search_terms"),
            (MarketData, "market_data"),
            (TrendsData, "trends_data"),
            (EngineeredFeature, "engineered_features"),
            (ModelRun, "model_runs"),
            (Prediction, "predictions"),
        ]:
            n = (await s.execute(select(func.count()).select_from(model))).scalar()
            print(f"  {name:24s} {n}")

        print("\n=== MARKET DATA BY SYMBOL ===")
        rows = (
            await s.execute(
                select(
                    MarketData.symbol,
                    func.count(),
                    func.min(MarketData.date),
                    func.max(MarketData.date),
                ).group_by(MarketData.symbol)
            )
        ).all()
        for sym, n, lo, hi in rows:
            print(f"  {sym:10s} rows={n:5d}  {lo} -> {hi}")

        print("\n=== SEARCH TERMS + TRENDS COVERAGE ===")
        terms = (await s.execute(select(SearchTerm))).scalars().all()
        for t in terms:
            r = (
                await s.execute(
                    select(
                        func.count(),
                        func.min(TrendsData.date),
                        func.max(TrendsData.date),
                    ).where(TrendsData.search_term_id == t.id)
                )
            ).one()
            print(f"  #{t.id} {t.term!r:22s} active={t.active} rows={r[0]:5d} {r[1]} -> {r[2]}")

        print("\n=== FEATURES COVERAGE ===")
        f = (
            await s.execute(
                select(
                    EngineeredFeature.symbol,
                    func.count(func.distinct(EngineeredFeature.date)),
                    func.min(EngineeredFeature.date),
                    func.max(EngineeredFeature.date),
                    func.count(func.distinct(EngineeredFeature.feature_name)),
                ).group_by(EngineeredFeature.symbol)
            )
        ).all()
        for sym, d, lo, hi, fn in f:
            print(f"  {sym:10s} dates={d:5d} {lo} -> {hi} feature_names={fn}")

        print("\n=== MODEL RUNS ===")
        mr = (await s.execute(select(ModelRun).order_by(ModelRun.id))).scalars().all()
        for m in mr:
            print(
                f"  #{m.id} {m.model_name:28s} task={m.task_type:14s} "
                f"sym={m.symbol} artifact={'Y' if m.artifact_path else 'N'} "
                f"train={m.training_start}->{m.training_end}"
            )

        print("\n=== LATEST MARKET ROW ===")
        row = (
            await s.execute(
                select(MarketData).where(MarketData.symbol == "^NSEI").order_by(MarketData.date.desc()).limit(3)
            )
        ).scalars().all()
        for m in row:
            print(f"  {m.date} close={m.close} ret={m.daily_return} vol={m.volume}")

        print("\n=== today (db) ===")
        print(" ", (await s.execute(text("SELECT CURRENT_DATE"))).scalar())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
