"""System health endpoints per spec § 18.9 / § 21."""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, cast, desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, Candle, LlmCallLog, Signal, SystemHealth
from app.schemas import LlmCallLogListItem, LlmCallLogOut, SystemHealthOut
from app.utils.time_utils import expected_latest_final_bar_start, utc_now

router = APIRouter()


@router.get("/health", response_model=list[SystemHealthOut])
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
    stmt = (
        select(
            func.date(LlmCallLog.created_at).label("day"),
            LlmCallLog.purpose,
            func.count().label("total"),
            func.sum(cast(LlmCallLog.cached, Integer)).label("cached_hits"),
            func.sum(LlmCallLog.input_tokens).label("input_tokens"),
            func.sum(LlmCallLog.output_tokens).label("output_tokens"),
            func.sum(LlmCallLog.cost_usd).label("cost_usd"),
        )
        .where(LlmCallLog.created_at >= since)
        .group_by("day", LlmCallLog.purpose)
        .order_by(desc("day"))
    )
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


@router.get("/llm-logs", response_model=list[LlmCallLogListItem])
def list_llm_logs(
    purpose: str | None = None,
    status: str | None = None,
    days: Annotated[int, Query(ge=1, le=90)] = 7,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    """List recent LLM calls (light shape for the table view).

    Use `GET /api/system/llm-logs/{id}` to fetch the full record including
    the prompt, input payload, raw response and thinking content.
    """
    since = utc_now() - timedelta(days=days)
    stmt = (
        select(LlmCallLog)
        .where(LlmCallLog.created_at >= since)
        .order_by(desc(LlmCallLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    if purpose:
        stmt = stmt.where(LlmCallLog.purpose == purpose)
    if status:
        stmt = stmt.where(LlmCallLog.status == status)
    return db.scalars(stmt).all()


@router.get("/llm-logs/{log_id}", response_model=LlmCallLogOut)
def get_llm_log(log_id: int, db: Session = Depends(get_db)):
    """Returns a single LLM call log with the full prompt / input / raw
    response / thinking content. This is the audit trail surface."""
    row = db.get(LlmCallLog, log_id)
    if row is None:
        raise HTTPException(status_code=404, detail="LlmCallLog not found")
    return row


@router.get("/data-freshness")
def data_freshness(db: Session = Depends(get_db)):
    """Returns the freshness skew for every (active asset, timeframe).

    Originally this issued 22 (assets) × 3 (timeframes) = 66 separate
    "latest candle" queries. We now do it in a single GROUP BY.
    """
    now = utc_now()
    timeframes = ("1d", "4h", "1h")

    assets = db.scalars(select(Asset).where(Asset.is_active.is_(True))).all()
    if not assets:
        return []

    symbols = [a.symbol for a in assets]
    latest_stmt = (
        select(
            Candle.symbol,
            Candle.timeframe,
            func.max(Candle.timestamp).label("ts"),
        )
        .where(
            Candle.symbol.in_(symbols),
            Candle.timeframe.in_(timeframes),
            Candle.is_final.is_(True),
        )
        .group_by(Candle.symbol, Candle.timeframe)
    )
    latest: dict[tuple[str, str], object] = {
        (r.symbol, r.timeframe): r.ts for r in db.execute(latest_stmt).all()
    }

    out: list[dict] = []
    for asset in assets:
        for tf in timeframes:
            expected = expected_latest_final_bar_start(asset.symbol, tf, now)
            actual = latest.get((asset.symbol, tf))
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
