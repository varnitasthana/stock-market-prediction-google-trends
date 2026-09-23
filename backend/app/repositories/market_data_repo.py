from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MarketData

#: Columns refreshed when an already-stored (symbol, date) row is re-ingested.
_UPDATABLE_COLUMNS = ("open", "high", "low", "close", "adj_close", "volume")


class MarketDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_symbol_and_date_range(self, symbol: str, start_date, end_date):
        stmt = (
            select(MarketData)
            .where(MarketData.symbol == symbol)
            .where(MarketData.date >= start_date)
            .where(MarketData.date <= end_date)
            .order_by(MarketData.date)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest(self, symbol: str, limit: int = 1):
        """Most recent rows for ``symbol``, newest first."""
        stmt = (
            select(MarketData)
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest_date(self, symbol: str):
        stmt = (
            select(MarketData.date)
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.date.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_coverage(self, symbol: str) -> dict:
        """Row count and first/last stored date for ``symbol``."""
        stmt = select(
            func.count(MarketData.id),
            func.min(MarketData.date),
            func.max(MarketData.date),
        ).where(MarketData.symbol == symbol)
        count, first_date, last_date = (await self.db.execute(stmt)).one()
        return {
            "row_count": int(count or 0),
            "first_date": first_date,
            "last_date": last_date,
        }

    async def get_close_series(self, symbol: str, start_date=None, end_date=None):
        """``(date, close)`` pairs in ascending date order."""
        stmt = select(MarketData.date, MarketData.close).where(MarketData.symbol == symbol)
        if start_date is not None:
            stmt = stmt.where(MarketData.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(MarketData.date <= end_date)
        stmt = stmt.order_by(MarketData.date)
        return (await self.db.execute(stmt)).all()

    async def bulk_insert(self, records: list[dict]):
        """Insert ``records`` ignoring duplicates.

        Kept as a thin wrapper over ``upsert`` so existing callers and tests that
        don't care about refreshing derived metrics still work.
        """
        await self.upsert(records)

    async def upsert(self, records: list[dict]) -> int:
        """Insert ``records``, refreshing any (symbol, date) row that exists.

        Returns the number of rows written. Re-ingesting an overlapping range is
        therefore idempotent instead of raising a unique-constraint error.
        """
        if not records:
            return 0

        self.db.expunge_all()

        stmt = pg_insert(MarketData).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_={col: getattr(stmt.excluded, col) for col in _UPDATABLE_COLUMNS},
        )
        await self.db.execute(stmt, execution_options={"synchronize_session": False})
        return len(records)

    async def update_metrics(self, symbol: str, metrics: dict) -> int:
        """Write ``{date: (daily_return, volatility)}`` back onto stored rows.

        Loads matching ORM objects and updates them in Python so the session
        never has to synchronize a bulk UPDATE that uses non-PK WHERE clauses.
        """
        if not metrics:
            return 0

        dates = list(metrics.keys())
        stmt = (
            select(MarketData)
            .where(MarketData.symbol == symbol)
            .where(MarketData.date.in_(dates))
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        updated = 0
        for row in rows:
            daily_return, volatility = metrics[row.date]
            row.daily_return = daily_return
            row.volatility = volatility
            updated += 1

        await self.db.flush()
        return updated

    async def get_by_symbol(self, symbol: str, limit: int = 100):
        stmt = (
            select(MarketData)
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_symbols(self) -> list[str]:
        stmt = select(MarketData.symbol).distinct().order_by(MarketData.symbol)
        return list((await self.db.execute(stmt)).scalars().all())
