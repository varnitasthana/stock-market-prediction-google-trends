import logging
from datetime import date, timedelta

from app.core.config import get_settings
from app.pipeline.market_pipeline import MarketIngestionService
from app.repositories.market_data_repo import MarketDataRepository
from app.utils import trading_calendar

logger = logging.getLogger(__name__)
settings = get_settings()

#: Extra days re-downloaded on refresh so the boundary row (whose "previous
#: close" changed) is recomputed rather than left with a stale return.
REFRESH_OVERLAP_DAYS = 7


class MarketDataService:
    def __init__(self, db):
        self.db = db
        self.repo = MarketDataRepository(db)

    async def get_market_data(self, symbol: str, start_date: date, end_date: date):
        return await self.repo.get_by_symbol_and_date_range(symbol, start_date, end_date)

    async def get_latest_date(self, symbol: str):
        return await self.repo.get_latest_date(symbol)

    async def get_recent(self, symbol: str, limit: int = 100):
        return await self.repo.get_by_symbol(symbol, limit=limit)

    async def list_available_symbols(self) -> list[dict]:
        """Every symbol held in the database, with its stored coverage."""
        symbols = await self.repo.list_symbols()
        rows = []
        for symbol in symbols:
            coverage = await self.repo.get_coverage(symbol)
            rows.append({"symbol": symbol, **coverage})
        return rows

    async def get_status(self, symbol: str) -> dict:
        """Snapshot of how current the stored history is for ``symbol``."""
        reference_now = trading_calendar.now_ist()
        today = reference_now.date()
        expected_session = trading_calendar.latest_expected_session(reference_now)

        coverage = await self.repo.get_coverage(symbol)
        last_stored = coverage["last_date"]

        if last_stored is None:
            sessions_behind = 0
            calendar_days_behind = None
            is_stale = True
            message = (
                f"No stored history for {symbol} yet. Refresh to download it "
                "from the market data provider."
            )
        else:
            sessions_behind = trading_calendar.business_days_between(last_stored, expected_session)
            calendar_days_behind = trading_calendar.days_between(last_stored, today)
            is_stale = sessions_behind > settings.stale_session_threshold
            if sessions_behind == 0:
                message = f"Up to date through the {last_stored} session."
            elif sessions_behind == 1:
                message = (
                    f"Stored data ends {last_stored} - one session behind "
                    f"({expected_session} is the latest expected close)."
                )
            else:
                message = (
                    f"Stored data ends {last_stored} - {sessions_behind} sessions behind "
                    f"({expected_session} is the latest expected close)."
                )

        latest_rows = await self.repo.get_latest(symbol, limit=1)
        has_derived_metrics = bool(latest_rows and latest_rows[0].daily_return is not None)

        return {
            "symbol": symbol,
            "today": today,
            "expected_session": expected_session,
            "last_stored_date": last_stored,
            "sessions_behind": sessions_behind,
            "is_stale": is_stale,
            "calendar_days_behind": calendar_days_behind,
            "row_count": coverage["row_count"],
            "first_stored_date": coverage["first_date"],
            "has_derived_metrics": has_derived_metrics,
            "last_checked_at": reference_now,
            "message": message,
        }

    async def get_live_quote(self, symbol: str) -> dict:
        """Latest stored close plus its change versus the prior session."""
        rows = await self.repo.get_latest(symbol, limit=2)
        now = trading_calendar.now_ist()

        if not rows:
            return {
                "symbol": symbol,
                "as_of": None,
                "price": None,
                "previous_close": None,
                "change": None,
                "change_percent": None,
                "day_high": None,
                "day_low": None,
                "day_open": None,
                "volume": None,
                "direction": "flat",
                "source": "database",
                "is_live": False,
                "retrieved_at": now,
            }

        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else None

        price = float(latest.close) if latest.close is not None else None
        previous_close = (
            float(previous.close) if previous is not None and previous.close is not None else None
        )

        change = None
        change_percent = None
        direction = "flat"
        if price is not None and previous_close not in (None, 0):
            change = price - previous_close
            change_percent = (change / previous_close) * 100.0
            if change > 0:
                direction = "up"
            elif change < 0:
                direction = "down"

        status = await self.get_status(symbol)

        return {
            "symbol": symbol,
            "as_of": latest.date,
            "price": price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": change_percent,
            "day_high": float(latest.high) if latest.high is not None else None,
            "day_low": float(latest.low) if latest.low is not None else None,
            "day_open": float(latest.open) if latest.open is not None else None,
            "volume": int(latest.volume) if latest.volume is not None else None,
            "direction": direction,
            "source": "database",
            "is_live": not status["is_stale"],
            "retrieved_at": now,
        }

    @staticmethod
    def _refresh_start(today: date, lookback_days: int, last_stored: date | None) -> date:
        """Earliest date to re-download for a refresh."""
        start = today - timedelta(days=lookback_days)
        if last_stored is not None and last_stored < start:
            # Bridge a larger gap, overlapping slightly so the boundary row's
            # derived return is recomputed against its true previous close.
            start = last_stored - timedelta(days=REFRESH_OVERLAP_DAYS)
        return start

    async def refresh(self, symbol: str, lookback_days: int = 30) -> dict:
        """Download the latest sessions for ``symbol`` and refresh derived metrics."""
        today = trading_calendar.today()
        coverage = await self.repo.get_coverage(symbol)
        start = self._refresh_start(today, lookback_days, coverage["last_date"])

        service = MarketIngestionService(self.db)
        try:
            result = await service.ingest(symbol, start.isoformat(), today.isoformat())
        except Exception as exc:  # provider/network failures must not surface as a 500
            logger.warning("Market refresh failed for %s: %s", symbol, exc)
            status = await self.get_status(symbol)
            return {
                "symbol": symbol,
                "requested_start": start,
                "requested_end": today,
                "downloaded_rows": 0,
                "new_rows": 0,
                "updated_rows": 0,
                "metrics_refreshed": 0,
                "latest_stored_date": coverage["last_date"],
                "status": status,
                "message": f"Could not reach the market data provider: {exc}",
            }

        status = await self.get_status(symbol)
        message = (
            f"Downloaded {result['total_records']} rows ({result['inserted']} new, "
            f"{result['updated']} refreshed). Now current through "
            f"{status['last_stored_date']}."
        )
        return {
            "symbol": symbol,
            "requested_start": start,
            "requested_end": today,
            "downloaded_rows": result["total_records"],
            "new_rows": result["inserted"],
            "updated_rows": result["updated"],
            "metrics_refreshed": result["metrics_refreshed"],
            "latest_stored_date": status["last_stored_date"],
            "status": status,
            "message": message,
        }
