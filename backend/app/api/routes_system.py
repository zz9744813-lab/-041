"""System health endpoints per spec § 18.9 / § 21."""
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, Candle, LlmCallLog, Signal, SystemHealth
from app.utils.time_utils import expected_latest_final_bar_start, utc_now

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    stmt = (
        select(SystemHealth)
        .order_by(desc(SystemHealth.started_at))
        .limit(50)
    )
    return db.scalars(stmt).all()


@router.get("/llm-stats")
def llm_stats(days: int = 7, db: Session = Depends(get_db)):
    since = utc_now() - timedelta(days=days)
    stmt = select(
        func.date(LlmCallLog.created_at).label("day"),
        LlmCallLog.purpose,
        func.count().label("total"),
        func.sum(func.cast(LlmCallLog.cached, type_=__import__("sqlalchemy").Integer)).label(
            "cached_hits"
        ),
        func.sum(LlmCallLog.input_tokens).label("input_tokens"),
        func.sum(LlmCallLog.output_tokens).label("output_tokens"),
        func.sum(LlmCallLog.cost_usd).label("cost_usd"),
    ).where(LlmCallLog.created_at >= since).group_by("day", LlmCallLog.purpose).order_by(desc("day"))
    rows = db.execute(stmt).all()
    return [
        {
            "day": str(r.day),
            "purpose": r.purpose,
            "total": int(r.total or 0),
            "cached_hits": int(r.cached_hits or 0),
            "input_tokens": int(r.input_tokens or 0),
            "output_tokens": int(r.output_tokens or 0),
            "cost_usd": str(r.cost_usd or 0),
        }
        for r in rows
    ]


@router.get("/data-freshness")
def data_freshness(db: Session = Depends(get_db)):
    now = utc_now()
    out = []
    assets = db.scalars(select(Asset).where(Asset.is_active.is_(True))).all()
    for asset in assets:
        for tf in ("1d", "4h", "1h"):
            expected = expected_latest_final_bar_start(asset.symbol, tf, now)
            stmt = (
                select(Candle.timestamp)
                .where(
                    Candle.symbol == asset.symbol,
                    Candle.timeframe == tf,
                    Candle.is_final.is_(True),
                )
                .order_by(desc(Candle.timestamp))
                .limit(1)
            )
            actual = db.scalars(stmt).first()
            skew_minutes = None
            if actual:
                skew_minutes = (expected - actual).total_seconds() / 60
            status = "STALE" if (skew_minutes is not None and skew_minutes > 120) else "FRESH"
            out.append(
                {
                    "symbol": asset.symbol,
                    "timeframe": tf,
                    "expected": expected.isoformat(),
                    "actual": actual.isoformat() if actual else None,
                    "skew_minutes": skew_minutes,
                    "status": status,
                }
            )
    return out


@router.get("/reject-reasons")
def reject_reasons(days: int = 7, db: Session = Depends(get_db)):
    since = utc_now() - timedelta(days=days)
    stmt = (
        select(Signal.reject_reason, func.count().label("n"))
        .where(Signal.status == "REJECTED", Signal.created_at >= since)
        .group_by(Signal.reject_reason)
        .order_by(desc(func.count()))
        .limit(15)
    )
    rows = db.execute(stmt).all()
    return [{"reason": r.reject_reason or "(unspecified)", "n": r.n} for r in rows]
