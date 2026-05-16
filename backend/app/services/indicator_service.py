"""Indicator calculation service - operates only on is_final=True candles.

Per spec § 8.2:
- Strict: only emit IndicatorSnapshot.based_on_closed_bar=True
- Skip if there aren't enough closed bars to compute an indicator
"""
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Candle, IndicatorSnapshot
from app.utils.time_utils import utc_now


def _to_dataframe(candles: list[Candle]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    rows = [
        {
            "timestamp": c.timestamp,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
        }
        for c in candles
    ]
    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)
    return rsi


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd = ema_fast - ema_slow
    signal_line = _ema(macd, signal)
    hist = macd - signal_line
    return macd, signal_line, hist


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return atr


def compute_for_symbol(
    db: Session,
    symbol: str,
    timeframe: str,
    lookback_bars: int = 300,
    now: datetime | None = None,
) -> dict:
    """Compute indicators for the latest closed bars and UPSERT into IndicatorSnapshot.

    Returns stats: {processed: int, latest_ts: str | None}
    """
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
        .limit(lookback_bars)
    )
    candles = list(db.scalars(stmt).all())
    candles.reverse()

    df = _to_dataframe(candles)
    if len(df) < 50:
        return {"processed": 0, "reason": f"insufficient_bars({len(df)})"}

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    df["ma20"] = close.rolling(20).mean()
    df["ma50"] = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()
    df["ema20"] = _ema(close, 20)
    df["ema50"] = _ema(close, 50)
    df["rsi14"] = _rsi(close, 14)
    macd, signal, hist = _macd(close)
    df["macd"] = macd
    df["macd_signal"] = signal
    df["macd_hist"] = hist
    df["atr14"] = _atr(df, 14)
    df["atr14_pct"] = (df["atr14"] / close).clip(lower=0)
    df["volume_ma20"] = volume.rolling(20).mean()

    # Simple support/resistance: rolling 20-bar low/high
    df["support_level"] = low.rolling(20).min()
    df["resistance_level"] = high.rolling(20).max()

    # Bollinger (20, 2)
    rolling_std = close.rolling(20).std()
    df["bbands_upper"] = df["ma20"] + 2 * rolling_std
    df["bbands_lower"] = df["ma20"] - 2 * rolling_std

    # Only persist the row(s) where MA200 is computable - that's our minimum bar
    valid = df.dropna(subset=["ma20", "rsi14"])
    processed = 0
    for _, row in valid.iterrows():
        values = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
            "based_on_closed_bar": True,
            "ma20": _opt(row["ma20"]),
            "ma50": _opt(row["ma50"]),
            "ma200": _opt(row["ma200"]),
            "ema20": _opt(row["ema20"]),
            "ema50": _opt(row["ema50"]),
            "rsi14": _opt(row["rsi14"]),
            "macd": _opt(row["macd"]),
            "macd_signal": _opt(row["macd_signal"]),
            "macd_hist": _opt(row["macd_hist"]),
            "atr14": _opt(row["atr14"]),
            "atr14_pct": _opt(row["atr14_pct"]),
            "volume_ma20": _opt(row["volume_ma20"]),
            "support_level": _opt(row["support_level"]),
            "resistance_level": _opt(row["resistance_level"]),
            "bbands_upper": _opt(row["bbands_upper"]),
            "bbands_lower": _opt(row["bbands_lower"]),
        }
        stmt = insert(IndicatorSnapshot).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={k: stmt.excluded[k] for k in values.keys() if k not in ("symbol", "timeframe", "timestamp")},
        )
        db.execute(stmt)
        processed += 1
    db.commit()

    last_ts = valid["timestamp"].iloc[-1] if not valid.empty else None
    return {
        "processed": processed,
        "latest_ts": last_ts.isoformat() if last_ts is not None else None,
    }


def _opt(v) -> Decimal | None:
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return Decimal(str(round(float(v), 6)))


def latest_snapshot(
    db: Session, symbol: str, timeframe: str, now: datetime | None = None
) -> IndicatorSnapshot | None:
    now = now or utc_now()
    stmt = (
        select(IndicatorSnapshot)
        .where(
            IndicatorSnapshot.symbol == symbol,
            IndicatorSnapshot.timeframe == timeframe,
            IndicatorSnapshot.based_on_closed_bar.is_(True),
            IndicatorSnapshot.timestamp <= now,
        )
        .order_by(IndicatorSnapshot.timestamp.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()
