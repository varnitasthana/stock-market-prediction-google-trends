"""IST-aware NSE trading-calendar helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
SESSION_SETTLE_HOUR_IST = 18

# NSE holidays relevant to the current data window. The provider remains the
# source of truth for rows, while this prevents weekday-only staleness counts.
KNOWN_NSE_HOLIDAYS = frozenset(
    {
        date(2026, 9, 14),
        date(2026, 10, 2),
    }
)


def now_ist() -> datetime:
    """Return the current time in IST."""
    return datetime.now(tz=IST)


def today() -> date:
    """Return today's date in IST."""
    return now_ist().date()


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def is_nse_holiday(day: date) -> bool:
    return day in KNOWN_NSE_HOLIDAYS


def is_session(day: date) -> bool:
    return not is_weekend(day) and not is_nse_holiday(day)


def _as_ist(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=IST)
    return moment.astimezone(IST)


def previous_business_day(day: date) -> date:
    """Return the latest NSE session strictly before ``day``."""
    cursor = day - timedelta(days=1)
    while not is_session(cursor):
        cursor -= timedelta(days=1)
    return cursor


def next_business_day(day: date) -> date:
    """Return the first NSE session strictly after ``day``."""
    cursor = day + timedelta(days=1)
    while not is_session(cursor):
        cursor += timedelta(days=1)
    return cursor


def latest_expected_session(reference: datetime | None = None) -> date:
    """Return the most recent session whose close should be published.

    A session is considered settled at 18:00 IST. A naive reference datetime is
    interpreted as IST so callers do not inherit the host timezone.
    """
    moment = _as_ist(reference) if reference is not None else now_ist()
    day = moment.date()

    if not is_session(day) or moment.hour < SESSION_SETTLE_HOUR_IST:
        return previous_business_day(day)
    return day


def business_days_between(start: date, end: date) -> int:
    """Count NSE sessions in ``(start, end]``; return zero if ``end <= start``."""
    if end <= start:
        return 0

    count = 0
    cursor = start
    while cursor < end:
        cursor += timedelta(days=1)
        if is_session(cursor):
            count += 1
    return count


def days_between(start: date, end: date) -> int:
    """Return the plain calendar-day difference."""
    return (end - start).days


def default_window(reference: date | None = None, lookback_days: int = 365) -> tuple[date, date]:
    """Return a window ending on the latest expected settled session."""
    end = reference or latest_expected_session()
    start = end - timedelta(days=lookback_days)
    return start, end
