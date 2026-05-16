"""Hermes Eyes - market data ingestion.

Per spec § 7 / § 8.1:
- All timestamps stored as UTC TIMESTAMPTZ
- Prices for US stocks always SPLIT_ADJUSTED
- is_final flag mandatory; non-final bars allowed for live display only
- (symbol, timeframe, timestamp) UPSERT; never mutate already-final OHLCV
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Iterable

import httpx
import yfinance as yf
from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Asset, Candle
from app.models.enums import Adjustment, Market
from app.utils.time_utils import is_final_for_timeframe, to_utc, utc_now


class CandleRow:
    """In-memory candle before persisting."""

    __slots__ = ("symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume")

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open_: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.open = open_
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


# ---- Provider abstraction ----

def fetch_candles_yfinance(
    symbol: str, timeframe: str, since: datetime, until: datetime
) -> list[CandleRow]:
    """Demo fallback. yfinance returns split-adjusted by default for stocks.

    Timeframe mapping: 1d->1d, 4h->90m (yf doesn't have 4h, we'd resample),
    1h->1h. For MVP we only fetch 1d via yfinance fallback.
    """
    yf_interval = {"1d": "1d", "1h": "1h", "4h": "1h"}.get(timeframe)
    if yf_interval is None:
        return []
    try:
        df = yf.Ticker(symbol).history(
            start=since.date(),
            end=(until + timedelta(days=1)).date(),
            interval=yf_interval,
            auto_adjust=True,  # split-adjusted
        )
    except Exception as e:
        logger.warning("yfinance fetch failed for {}: {}", symbol, e)
        return []

    if df.empty:
        return []

    rows: list[CandleRow] = []
    for ts, r in df.iterrows():
        ts_utc = to_utc(ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts)
        rows.append(
            CandleRow(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts_utc,
                open_=Decimal(str(r["Open"])),
                high=Decimal(str(r["High"])),
                low=Decimal(str(r["Low"])),
                close=Decimal(str(r["Close"])),
                volume=Decimal(str(r.get("Volume", 0))),
            )
        )
    return rows


def fetch_candles_alpaca(
    symbol: str,
    timeframe: str,
    since: datetime,
    until: datetime,
    market: Market,
) -> list[CandleRow]:
    """Alpaca Market Data v2 fetcher. Returns empty list if no API key configured."""
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_api_secret:
        return []

    headers = {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
    }

    tf_map = {"1d": "1Day", "4h": "4Hour", "1h": "1Hour"}
    tf = tf_map.get(timeframe)
    if tf is None:
        return []

    if market == Market.CRYPTO:
        url = "https://data.alpaca.markets/v1beta3/crypto/us/bars"
        params = {
            "symbols": symbol,
            "timeframe": tf,
            "start": since.isoformat().replace("+00:00", "Z"),
            "end": until.isoformat().replace("+00:00", "Z"),
            "limit": 10000,
        }
    else:
        url = "https://data.alpaca.markets/v2/stocks/bars"
        params = {
            "symbols": symbol,
            "timeframe": tf,
            "adjustment": "split",  # spec § 7.6 SPLIT_ADJUSTED
            "start": since.isoformat().replace("+00:00", "Z"),
            "end": until.isoformat().replace("+00:00", "Z"),
            "limit": 10000,
            "feed": "iex",
        }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("Alpaca fetch failed for {}/{}: {}", symbol, timeframe, e)
        return []

    bars = data.get("bars", {}).get(symbol, []) if isinstance(data.get("bars"), dict) else data.get(
        "bars", []
    )
    rows: list[CandleRow] = []
    for b in bars:
        rows.append(
            CandleRow(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=to_utc(datetime.fromisoformat(b["t"].replace("Z", "+00:00"))),
                open_=Decimal(str(b["o"])),
                high=Decimal(str(b["h"])),
                low=Decimal(str(b["l"])),
                close=Decimal(str(b["c"])),
                volume=Decimal(str(b.get("v", 0))),
            )
        )
    return rows


# ---- UPSERT logic ----

def upsert_candles(
    db: Session,
    rows: Iterable[CandleRow],
    source: str,
    adjustment: Adjustment,
    now: datetime | None = None,
) -> dict:
    """Insert/update candle rows.

    Hard rule (spec § 7.6): never mutate OHLCV of an already-final bar.
    We achieve this with ON CONFLICT DO UPDATE WHERE candles.is_final = false.

    Returns stats dict.
    """
    now = now or utc_now()
    inserted = 0
    updated = 0
    skipped_final = 0

    for r in rows:
        is_final = is_final_for_timeframe(r.timestamp, r.timeframe, now)

        stmt = insert(Candle).values(
            symbol=r.symbol,
            timeframe=r.timeframe,
            timestamp=r.timestamp,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            volume=r.volume,
            source=source,
            adjustment=adjustment.value,
            is_final=is_final,
        )

        # ON CONFLICT: only update if existing row is NOT final
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "is_final": stmt.excluded.is_final,
                "updated_at": now,
            },
            where=Candle.is_final.is_(False),
        )
        result = db.execute(stmt)
        if result.rowcount == 0:
            # Either inserted (rowcount 1) or skipped because already final
            # PG returns 0 for "no row affected by UPDATE part" but inserts return rowcount=1.
            # To distinguish, we'd need RETURNING; for stats simplicity:
            skipped_final += 1
        else:
            inserted += 1

    db.commit()
    logger.info(
        "candle upsert: source={} adjustment={} processed={} skipped_final={}",
        source,
        adjustment.value,
        inserted,
        skipped_final,
    )
    return {"processed": inserted, "skipped_final": skipped_final}


# ---- Public API ----

def sync_symbol(
    db: Session,
    asset: Asset,
    timeframes: list[str] = None,
    lookback_days: int = 365,
    now: datetime | None = None,
) -> dict:
    """Pull candles for one asset across the given timeframes."""
    now = now or utc_now()
    timeframes = timeframes or ["1d", "4h", "1h"]
    until = now
    since = now - timedelta(days=lookback_days)

    stats: dict = {"symbol": asset.symbol, "timeframes": {}}
    for tf in timeframes:
        rows = fetch_candles_alpaca(asset.symbol, tf, since, until, Market(asset.market))
        if not rows:
            # Fallback to yfinance for daily; 4h/1h may be empty
            rows = fetch_candles_yfinance(asset.symbol, tf, since, until)

        if not rows:
            stats["timeframes"][tf] = {"processed": 0, "fetched": 0}
            continue

        s = upsert_candles(db, rows, source="alpaca-or-yf", adjustment=Adjustment.SPLIT_ADJUSTED, now=now)
        s["fetched"] = len(rows)
        stats["timeframes"][tf] = s

    return stats


def latest_final_bar(db: Session, symbol: str, timeframe: str, now: datetime | None = None) -> Candle | None:
    """Return the latest is_final=True bar at or before `now`."""
    now = now or utc_now()
    stmt = (
        select(Candle)
        .where(
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
            Candle.is_final.is_(True),
            Candle.timestamp <= now,
        )
        .order_by(Candle.timestamp.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def candles_until(
    db: Session,
    symbol: str,
    timeframe: str,
    now: datetime,
    limit: int = 300,
) -> list[Candle]:
    """Return up to `limit` final bars at or before `now`, ascending order.

    For backtest support per spec § 22.
    """
    stmt = (
        select(Candle)
        .where(
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
            Candle.is_final.is_(True),
            Candle.timestamp <= now,
        )
        .order_by(Candle.timestamp.desc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    rows.reverse()
    return rows
