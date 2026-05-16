"""Market regime classification per spec § 13."""
from datetime import UTC, datetime
from decimal import Decimal

import yfinance as yf
from loguru import logger
from sqlalchemy.orm import Session

from app.models import MarketRegime
from app.models.enums import MarketRegimeEnum
from app.services.indicator_service import latest_snapshot
from app.services.data_service import latest_final_bar
from app.utils.time_utils import utc_now


def fetch_vix(now: datetime | None = None) -> Decimal | None:
    """Best-effort VIX fetch via yfinance."""
    try:
        df = yf.Ticker("^VIX").history(period="5d", interval="1d")
        if df.empty:
            return None
        latest = df["Close"].iloc[-1]
        return Decimal(str(round(float(latest), 4)))
    except Exception as e:
        logger.warning("vix fetch failed: {}", e)
        return None


def classify(db: Session, now: datetime | None = None) -> MarketRegime | None:
    """Classify and persist a MarketRegime row.

    Inputs: SPY indicators (1d), VIX level, BTC indicators (1d).
    Returns the persisted row, or None if insufficient data.
    """
    now = now or utc_now()

    spy_ind = latest_snapshot(db, "SPY", "1d", now)
    btc_ind = latest_snapshot(db, "BTC-USD", "1d", now)
    spy_bar = latest_final_bar(db, "SPY", "1d", now)
    btc_bar = latest_final_bar(db, "BTC-USD", "1d", now)

    if spy_ind is None or spy_bar is None:
        logger.warning("regime: spy data missing, skipping")
        return None

    spy_close = float(spy_bar.close)
    spy_ma200 = float(spy_ind.ma200) if spy_ind.ma200 else None
    spy_ma50 = float(spy_ind.ma50) if spy_ind.ma50 else None

    btc_close = float(btc_bar.close) if btc_bar else None
    btc_ma200 = float(btc_ind.ma200) if btc_ind and btc_ind.ma200 else None

    spy_above_ma200 = spy_ma200 is not None and spy_close > spy_ma200
    spy_above_ma50 = spy_ma50 is not None and spy_close > spy_ma50
    spy_ma50_above_ma200 = (
        spy_ma50 is not None and spy_ma200 is not None and spy_ma50 > spy_ma200
    )
    btc_above_ma200 = (
        btc_close is not None and btc_ma200 is not None and btc_close > btc_ma200
    )

    vix = fetch_vix(now)

    regime: MarketRegimeEnum
    notes_parts: list[str] = []

    if vix is not None and vix >= 30:
        regime = MarketRegimeEnum.HIGH_VOL_PANIC
        notes_parts.append(f"vix={vix} >= 30")
    elif spy_above_ma200 and spy_above_ma50 and spy_ma50_above_ma200 and btc_above_ma200:
        regime = MarketRegimeEnum.STRONG_BULL
    elif spy_above_ma200 and spy_above_ma50:
        regime = MarketRegimeEnum.MILD_BULL
    elif (
        not spy_above_ma200
        and not spy_above_ma50
        and spy_ma50 is not None
        and spy_ma200 is not None
        and spy_ma50 < spy_ma200
    ):
        regime = MarketRegimeEnum.STRONG_BEAR
    elif not spy_above_ma200:
        regime = MarketRegimeEnum.MILD_BEAR
    else:
        regime = MarketRegimeEnum.RANGE

    notes_parts.append(
        f"spy_close={spy_close:.2f} ma50={spy_ma50} ma200={spy_ma200} "
        f"btc_above_ma200={btc_above_ma200} vix={vix}"
    )

    row = MarketRegime(
        timestamp=now.replace(microsecond=0),
        regime=regime.value,
        spy_above_ma200=spy_above_ma200,
        spy_above_ma50=spy_above_ma50,
        vix_level=vix,
        btc_above_ma200=btc_above_ma200,
        notes=" | ".join(notes_parts),
    )
    db.merge(row)
    db.commit()
    return row


# ---- Risk parameter mapping per spec § 13.3 ----

REGIME_LIMITS: dict[str, dict] = {
    MarketRegimeEnum.STRONG_BULL.value: {
        "allow_new": True,
        "max_total_pct": Decimal("0.80"),
        "max_per_trade_risk_pct": Decimal("0.01"),
    },
    MarketRegimeEnum.MILD_BULL.value: {
        "allow_new": True,
        "max_total_pct": Decimal("0.70"),
        "max_per_trade_risk_pct": Decimal("0.01"),
    },
    MarketRegimeEnum.RANGE.value: {
        "allow_new": True,
        "max_total_pct": Decimal("0.50"),
        "max_per_trade_risk_pct": Decimal("0.007"),
    },
    MarketRegimeEnum.MILD_BEAR.value: {
        "allow_new": True,
        "max_total_pct": Decimal("0.40"),
        "max_per_trade_risk_pct": Decimal("0.005"),
    },
    MarketRegimeEnum.STRONG_BEAR.value: {
        "allow_new": False,
        "max_total_pct": Decimal("0"),
        "max_per_trade_risk_pct": Decimal("0"),
    },
    MarketRegimeEnum.HIGH_VOL_PANIC.value: {
        "allow_new": False,
        "max_total_pct": Decimal("0"),
        "max_per_trade_risk_pct": Decimal("0"),
    },
}


def limits_for(regime_name: str | None) -> dict:
    if regime_name is None:
        return REGIME_LIMITS[MarketRegimeEnum.MILD_BULL.value]
    return REGIME_LIMITS.get(regime_name, REGIME_LIMITS[MarketRegimeEnum.MILD_BULL.value])
