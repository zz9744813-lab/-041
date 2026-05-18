"""Models endpoints per spec § 18.8."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ModelStat, StrategyModel, Trade
from app.schemas import (
    ModelStatOut,
    ModelSummaryRow,
    RMultipleScatterPoint,
    StrategyModelOut,
)

router = APIRouter()


@router.get("", response_model=list[StrategyModelOut])
def list_models(db: Session = Depends(get_db)):
    return db.scalars(select(StrategyModel).order_by(StrategyModel.name)).all()


@router.get("/summary", response_model=list[ModelSummaryRow])
def models_summary(
    window: str = "LAST_30D",
    recent_trades_limit: Annotated[int, Query(ge=0, le=200)] = 50,
    db: Session = Depends(get_db),
):
    """Single endpoint that joins StrategyModel + ModelStat(window) + recent
    R-multiple points per model. Replaces 1 + N + N round-trips from the UI.
    """
    models = list(db.scalars(select(StrategyModel).order_by(StrategyModel.name)).all())
    names = [m.name for m in models]
    if not names:
        return []

    stats = {
        s.model_name: s
        for s in db.scalars(
            select(ModelStat).where(
                ModelStat.model_name.in_(names),
                ModelStat.window == window,
            )
        ).all()
    }

    # Pre-fetch recent trades (only the columns the scatter chart needs).
    recent: dict[str, list[RMultipleScatterPoint]] = {n: [] for n in names}
    if recent_trades_limit > 0:
        # We pull recent_trades_limit per model with one window function in
        # a sub-query. Falls back to a per-model query if the dialect is
        # SQLite (no row_number support without extension).
        try:
            from sqlalchemy import func, literal_column

            rn = (
                func.row_number()
                .over(
                    partition_by=Trade.model_name,
                    order_by=desc(Trade.exit_time),
                )
                .label("rn")
            )
            sub = (
                select(
                    Trade.model_name,
                    Trade.exit_time,
                    Trade.realized_r_multiple,
                    Trade.pnl_pct,
                    Trade.symbol,
                    Trade.exit_reason,
                    rn,
                )
                .where(
                    Trade.model_name.in_(names),
                    Trade.status == "CLOSED",
                )
            ).subquery()
            stmt = (
                select(sub)
                .where(literal_column("rn") <= recent_trades_limit)
                .order_by(sub.c.exit_time.desc())
            )
            for row in db.execute(stmt).all():
                recent[row.model_name].append(
                    RMultipleScatterPoint(
                        exit_time=row.exit_time,
                        realized_r_multiple=row.realized_r_multiple,
                        pnl_pct=row.pnl_pct,
                        symbol=row.symbol,
                        exit_reason=row.exit_reason,
                    )
                )
        except Exception:
            # Per-model fallback - costlier but always works.
            for n in names:
                rows = db.scalars(
                    select(Trade)
                    .where(Trade.model_name == n, Trade.status == "CLOSED")
                    .order_by(desc(Trade.exit_time))
                    .limit(recent_trades_limit)
                ).all()
                recent[n] = [
                    RMultipleScatterPoint(
                        exit_time=t.exit_time,
                        realized_r_multiple=t.realized_r_multiple,
                        pnl_pct=t.pnl_pct,
                        symbol=t.symbol,
                        exit_reason=t.exit_reason,
                    )
                    for t in rows
                    if t.exit_time is not None
                ]

    out: list[ModelSummaryRow] = []
    for m in models:
        stat = stats.get(m.name)
        out.append(
            ModelSummaryRow(
                name=m.name,
                description=m.description,
                weight=m.weight,
                is_active=m.is_active,
                auto_adjust_weight=m.auto_adjust_weight,
                stat=ModelStatOut.model_validate(stat) if stat else None,
                recent_r_multiples=recent.get(m.name, []),
            )
        )
    return out


@router.get("/{name}/stats", response_model=ModelStatOut)
def model_stats(name: str, window: str = "LAST_30D", db: Session = Depends(get_db)):
    stmt = select(ModelStat).where(ModelStat.model_name == name, ModelStat.window == window)
    s = db.scalars(stmt).first()
    if not s:
        raise HTTPException(status_code=404, detail="No stats yet")
    return s


@router.patch("/{name}", response_model=StrategyModelOut)
def update_model(
    name: str,
    weight: float | None = None,
    auto_adjust: bool | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(StrategyModel).where(StrategyModel.name == name)
    m = db.scalars(stmt).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    if weight is not None:
        m.weight = weight
    if auto_adjust is not None:
        m.auto_adjust_weight = auto_adjust
    if is_active is not None:
        m.is_active = is_active
    db.commit()
    db.refresh(m)
    return m


@router.get("/{name}/recent-trades", response_model=list[RMultipleScatterPoint])
def recent_trades(name: str, limit: int = 50, db: Session = Depends(get_db)):
    """Light shape: only the fields the R-multiple scatter chart needs."""
    stmt = (
        select(Trade)
        .where(Trade.model_name == name, Trade.status == "CLOSED")
        .order_by(desc(Trade.exit_time))
        .limit(limit)
    )
    out: list[RMultipleScatterPoint] = []
    for t in db.scalars(stmt).all():
        if t.exit_time is None:
            continue
        out.append(
            RMultipleScatterPoint(
                exit_time=t.exit_time,
                realized_r_multiple=t.realized_r_multiple,
                pnl_pct=t.pnl_pct,
                symbol=t.symbol,
                exit_reason=t.exit_reason,
            )
        )
    return out
