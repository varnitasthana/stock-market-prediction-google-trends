from datetime import date, datetime
from types import SimpleNamespace

from app.utils import trading_calendar
from app.workers.scheduled_tasks import select_market_ingestion_window


def test_market_ingestion_uses_next_settled_session():
    settings = SimpleNamespace(
        resolved_start_date=lambda end: date(2026, 1, 1),
    )
    reference = datetime(2026, 11, 23, 18, 0, tzinfo=trading_calendar.IST)

    window = select_market_ingestion_window(
        date(2026, 11, 20),
        settings,
        reference,
    )

    assert window == (date(2026, 11, 23), date(2026, 11, 23))


def test_market_ingestion_refreshes_boundary_row():
    settings = SimpleNamespace(
        resolved_start_date=lambda end: date(2026, 1, 1),
    )
    reference = datetime(2026, 11, 24, 18, 0, tzinfo=trading_calendar.IST)

    window = select_market_ingestion_window(
        date(2026, 11, 24),
        settings,
        reference,
    )

    assert window == (date(2026, 11, 23), date(2026, 11, 24))
