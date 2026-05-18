"""System health endpoints per spec § 18.9 / § 21."""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import Float, Integer, cast, desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, Candle, LlmCallLog, Signal, SignalSkip, SystemHealth
from app.schemas import (
    LlmCallLogListItem,
    LlmCallLogOut,
    SignalSkipOut,
    SystemHealthListItem,
    SystemHealthOut,
)
from app.utils.time_utils import expected_latest_final_bar_start, utc_now

router = APIRouter()


@router.get("/health", response_model=list[SystemHealthListItem])
def health(db: Session = Depends(get_db)):
    """Light shape: omits the per-job `stats` dict to keep the polled
    payload small. Use `GET /api/system/health/{id}` for the full record."""
    stmt = (
        select(SystemHealth)
        .order_by(desc(SystemHealth.started_at))
        .limit(50)
    )
    return db.scalars(stmt).all()


@router.get("/health/{health_id}", response_model=SystemHealthOut)
def health_detail(health_id: int, db: Session = Depends(get_db)):
    row = db.get(SystemHealth, health_id)
    if not row:
        raise HTTPException(status_code=404, detail="SystemHealth row not found")
    return row


@router.get("/llm-stats")
def llm_stats(days: int = 7, db: Session = Depends(get_db)):
    """Daily aggregates per purpose: total / cached / cost / latency P50/P95
    / success_rate / avg_attempts."""
    since = utc_now() - timedelta(days=days)

    # P50/P95 are dialect-specific; we approximate with a portable expression.
    # Postgres has percentile_cont; SQLite doesn't, so we fall back to the
    # AVG of MIN+MAX as a coarse heuristic for SQLite environments.
    dialect_name = db.bind.dialect.name if db.bind else ""
    if dialect_name == "postgresql":
        p50 = func.percentile_cont(0.5).within_group(LlmCallLog.latency_ms.asc()).label("p50")
        p95 = func.percentile_cont(0.95).within_group(LlmCallLog.latency_ms.asc()).label("p95")
    else:
        p50 = func.avg(LlmCallLog.latency_ms).label("p50")
        p95 = func.max(LlmCallLog.latency_ms).label("p95")

    success_count = func.sum(
        cast(LlmCallLog.status == "SUCCESS", Integer)
    ).label("success_count")

    stmt = (
        select(
            func.date(LlmCallLog.created_at).label("day"),
            LlmCallLog.purpose,
            func.count().label("total"),
            func.sum(cast(LlmCallLog.cached, Integer)).label("cached_hits"),
            func.sum(LlmCallLog.input_tokens).label("input_tokens"),
            func.sum(LlmCallLog.output_tokens).label("output_tokens"),
            func.sum(LlmCallLog.cost_usd).label("cost_usd"),
            func.avg(cast(LlmCallLog.attempts, Float)).label("avg_attempts"),
            success_count,
            p50,
            p95,
        )
        .where(LlmCallLog.created_at >= since)
        .group_by("day", LlmCallLog.purpose)
        .order_by(desc("day"))
    )
    rows = db.execute(stmt).all()
    out = []
    for r in rows:
        total = int(r.total or 0)
        succ = int(r.success_count or 0)
        out.append(
            {
                "day": str(r.day),
                "purpose": r.purpose,
                "total": total,
                "cached_hits": int(r.cached_hits or 0),
                "input_tokens": int(r.input_tokens or 0),
                "output_tokens": int(r.output_tokens or 0),
                "cost_usd": str(r.cost_usd or 0),
                "avg_attempts": float(r.avg_attempts) if r.avg_attempts is not None else None,
                "success_rate": (succ / total) if total else None,
                "latency_p50_ms": float(r.p50) if r.p50 is not None else None,
                "latency_p95_ms": float(r.p95) if r.p95 is not None else None,
            }
        )
    return out


@router.get("/llm-logs", response_model=list[LlmCallLogListItem])
def list_llm_logs(
    purpose: str | None = None,
    status: str | None = None,
    symbol: str | None = None,
    days: Annotated[int, Query(ge=1, le=90)] = 7,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    """List recent LLM calls (light shape)."""
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
    if symbol:
        stmt = stmt.where(LlmCallLog.symbol == symbol)
    return db.scalars(stmt).all()


@router.get("/llm-logs/{log_id}", response_model=LlmCallLogOut)
def get_llm_log(log_id: int, response: Response, db: Session = Depends(get_db)):
    """Full prompt / input / raw response / thinking / attempt_history.

    Cached aggressively because LlmCallLog rows are append-only.
    """
    row = db.get(LlmCallLog, log_id)
    if row is None:
        raise HTTPException(status_code=404, detail="LlmCallLog not found")
    response.headers["Cache-Control"] = "private, max-age=3600, immutable"
    return row


@router.get("/llm-cost-attribution")
def llm_cost_attribution(
    days: Annotated[int, Query(ge=1, le=90)] = 7,
    group: Annotated[str, Query(pattern="^(symbol|model|purpose)$")] = "symbol",
    db: Session = Depends(get_db),
):
    """Returns cost / token totals grouped by `symbol`, `model`, or `purpose`.

    Used by the /llm/cost-attribution page to answer "where is the LLM
    budget going?" questions. Cached calls (cost_usd=0) are excluded.
    """
    since = utc_now() - timedelta(days=days)
    if group == "symbol":
        key = LlmCallLog.symbol
    elif group == "model":
        key = LlmCallLog.model
    else:
        key = LlmCallLog.purpose
    stmt = (
        select(
            key.label("key"),
            func.count().label("calls"),
            func.sum(LlmCallLog.input_tokens).label("input_tokens"),
            func.sum(LlmCallLog.output_tokens).label("output_tokens"),
            func.sum(LlmCallLog.cost_usd).label("cost_usd"),
        )
        .where(
            LlmCallLog.created_at >= since,
            LlmCallLog.cached.is_(False),
            LlmCallLog.status == "SUCCESS",
        )
        .group_by(key)
        .order_by(desc(func.coalesce(func.sum(LlmCallLog.cost_usd), 0)))
        .limit(100)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "key": (r.key or "(unknown)"),
            "calls": int(r.calls or 0),
            "input_tokens": int(r.input_tokens or 0),
            "output_tokens": int(r.output_tokens or 0),
            "cost_usd": str(r.cost_usd or 0),
        }
        for r in rows
    ]


@router.get("/llm-budget")
def llm_budget(db: Session = Depends(get_db)):
    """Returns today's spend + the configured cap so the UI can show a
    progress bar / warning."""
    from app.config import get_settings
    from app.services.llm_client import todays_cost_usd

    settings = get_settings()
    spent = todays_cost_usd(db)
    cap = settings.max_daily_llm_cost_usd
    return {
        "spent_usd": str(spent),
        "cap_usd": str(cap),
        "remaining_usd": str(cap - spent) if cap > 0 else None,
        "enforced": cap > 0,
    }


@router.get("/data-freshness")
def data_freshness(db: Session = Depends(get_db)):
    """Returns the freshness skew for every (active asset, timeframe).

    Single GROUP BY for all (symbol, timeframe) pairs.
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


@router.get("/skip-reasons")
def skip_reasons(days: int = 7, db: Session = Depends(get_db)):
    """Why we *didn't* generate a signal for a symbol.

    Surfaces SignalSkip rows aggregated by reason. Click-throughable to
    `/api/system/skips?reason=...&days=...` for the full list.
    """
    since = utc_now() - timedelta(days=days)
    stmt = (
        select(SignalSkip.reason, func.count().label("n"))
        .where(SignalSkip.created_at >= since)
        .group_by(SignalSkip.reason)
        .order_by(desc(func.count()))
    )
    rows = db.execute(stmt).all()
    return [{"reason": r.reason, "n": r.n} for r in rows]


@router.get("/skips", response_model=list[SignalSkipOut])
def list_skips(
    reason: str | None = None,
    symbol: str | None = None,
    days: Annotated[int, Query(ge=1, le=90)] = 7,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    since = utc_now() - timedelta(days=days)
    stmt = (
        select(SignalSkip)
        .where(SignalSkip.created_at >= since)
        .order_by(desc(SignalSkip.created_at))
        .offset(offset)
        .limit(limit)
    )
    if reason:
        stmt = stmt.where(SignalSkip.reason == reason)
    if symbol:
        stmt = stmt.where(SignalSkip.symbol == symbol)
    return db.scalars(stmt).all()
