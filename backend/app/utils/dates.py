from datetime import date, datetime

import pandas as pd


def ensure_date(d) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return date.fromisoformat(d)
    raise TypeError(f"Cannot convert {type(d)} to date")


def filter_trading_dates(dates: list[date]) -> list[date]:
    weekdays = [d for d in dates if d.weekday() < 5]
    return sorted(set(weekdays))


def get_date_range(start: date, end: date) -> list[date]:
    return pd.date_range(start=start, end=end, freq="B").tolist()
