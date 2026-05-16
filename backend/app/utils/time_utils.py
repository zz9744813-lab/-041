"""Time utilities - UTC normalization, is_final detection, market calendar."""
from datetime import UTC, datetime, timedelta

import pandas_market_calendars as mcal

_NYSE = mcal.get_calendar("NYSE")


def utc_now() -> datetime:
    """Single source for current UTC time. Tests can monkeypatch this."""
    return datetime.now(UTC)


def to_utc(ts: datetime) -> datetime:
    """Force a datetime into UTC."""
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


def is_us_trading_day(now: datetime) -> bool:
    """Returns True if NYSE has a session on the given UTC date (in ET terms)."""
    et_date = now.astimezone(UTC).date()
    schedule = _NYSE.schedule(start_date=et_date, end_date=et_date)
    return not schedule.empty


def is_us_market_open(now: datetime) -> bool:
    """Returns True if NYSE is currently in session for now (UTC)."""
    et_date = now.astimezone(UTC).date()
    schedule = _NYSE.schedule(start_date=et_date, end_date=et_date)
    if schedule.empty:
        return False
    open_time = schedule.iloc[0]["market_open"].to_pydatetime()
    close_time = schedule.iloc[0]["market_close"].to_pydatetime()
    return open_time <= now <= close_time


def is_final_for_timeframe(bar_start: datetime, timeframe: str, now: datetime) -> bool:
    """Whether a bar starting at `bar_start` for the given `timeframe` is closed
    relative to `now`. All times in UTC.

    Per spec § 7.6:
      1d: bar_end = bar_start + 1 day
      4h: bar_end = bar_start + 4h
      1h: bar_end = bar_start + 1h
    A bar is final when now >= bar_end.
    """
    bar_start = to_utc(bar_start)
    now = to_utc(now)
    delta_map = {
        "1d": timedelta(days=1),
        "4h": timedelta(hours=4),
        "1h": timedelta(hours=1),
    }
    delta = delta_map.get(timeframe)
    if delta is None:
        raise ValueError(f"Unknown timeframe: {timeframe}")
    bar_end = bar_start + delta
    return now >= bar_end


def expected_latest_final_bar_start(symbol: str, timeframe: str, now: datetime) -> datetime:
    """The bar_start of the latest bar that should be final by `now`.

    Used for /system data freshness check.
    """
    now = to_utc(now)
    delta_map = {
        "1d": timedelta(days=1),
        "4h": timedelta(hours=4),
        "1h": timedelta(hours=1),
    }
    delta = delta_map[timeframe]
    # Round down to bar boundary
    seconds = int(delta.total_seconds())
    epoch = int(now.timestamp())
    last_boundary = (epoch // seconds) * seconds
    last_final_start = datetime.fromtimestamp(last_boundary, tz=UTC) - delta
    return last_final_start
