"""Model statistics + weight adjustment per spec § 12.5 / § 23."""
from datetime import datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import ModelStat, StrategyModel, Trade
from app.utils.time_utils import utc_now


def sample_quality(n: int) -> str:
    if n < 10:
        return "INSUFFICIENT"
    if n < 30:
        return "LOW"
    if n < 100:
        return "ADEQUATE"
    return "GOOD"


def _compute_window_stats(
    db: Session, model_name: str, since: datetime | None
) -> dict:
    stmt = select(Trade).where(Trade.model_name == model_name, Trade.status == "CLOSED")
    if since is not None:
        stmt = stmt.where(Trade.exit_time >= since)
    trades = list(db.scalars(stmt).all())
    n = len(trades)
    if n == 0:
        return {"trade_count": 0, "win_count": 0, "loss_count": 0, "sample_quality": sample_quality(0)}

    wins = [t for t in trades if (t.pnl_amount or 0) > 0]
    losses = [t for t in trades if (t.pnl_amount or 0) <= 0]
    win_rate = Decimal(len(wins)) / Decimal(n)

    avg_win_pct = (
        sum(((t.pnl_pct or Decimal("0")) for t in wins), Decimal("0")) / max(len(wins), 1)
        if wins
        else None
    )
    avg_loss_pct = (
        sum(((t.pnl_pct or Decimal("0")) for t in losses), Decimal("0")) / max(len(losses), 1)
        if losses
        else None
    )

    total_win_pnl = sum((t.pnl_amount or Decimal("0") for t in wins), Decimal("0"))
    total_loss_pnl_abs = abs(sum((t.pnl_amount or Decimal("0") for t in losses), Decimal("0")))
    profit_factor = total_win_pnl / total_loss_pnl_abs if total_loss_pnl_abs > 0 else None

    expectancy = None
    if avg_win_pct is not None and avg_loss_pct is not None:
        loss_rate = Decimal("1") - win_rate
        expectancy = win_rate * avg_win_pct - loss_rate * abs(avg_loss_pct)

    r_multiples = [t.realized_r_multiple for t in trades if t.realized_r_multiple is not None]
    avg_r = (sum(r_multiples, Decimal("0")) / Decimal(len(r_multiples))) if r_multiples else None

    return {
        "trade_count": n,
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": win_rate.quantize(Decimal("0.0001")),
        "avg_win_pct": avg_win_pct.quantize(Decimal("0.0001")) if avg_win_pct is not None else None,
        "avg_loss_pct": avg_loss_pct.quantize(Decimal("0.0001")) if avg_loss_pct is not None else None,
        "profit_factor": profit_factor.quantize(Decimal("0.0001")) if profit_factor is not None else None,
        "expectancy": expectancy.quantize(Decimal("0.0001")) if expectancy is not None else None,
        "avg_r_multiple": avg_r.quantize(Decimal("0.0001")) if avg_r is not None else None,
        "sample_quality": sample_quality(n),
    }


def update_stats_for_model(
    db: Session, model_name: str, now: datetime | None = None
) -> dict[str, dict]:
    now = now or utc_now()
    windows = {
        "ALL_TIME": None,
        "LAST_30D": now - timedelta(days=30),
        "LAST_90D": now - timedelta(days=90),
    }
    out: dict[str, dict] = {}
    for window, since in windows.items():
        stats = _compute_window_stats(db, model_name, since)
        stmt = insert(ModelStat).values(
            model_name=model_name,
            window=window,
            last_computed_at=now,
            **stats,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["model_name", "window"],
            set_={
                "last_computed_at": now,
                **stats,
            },
        )
        db.execute(stmt)
        out[window] = stats
    db.commit()
    return out


def adjust_weight(
    db: Session, model_name: str, now: datetime | None = None
) -> Decimal:
    """Per spec § 12.5 - auto-adjust based on LAST_30D performance."""
    now = now or utc_now()
    stat = db.scalars(
        select(ModelStat).where(
            ModelStat.model_name == model_name, ModelStat.window == "LAST_30D"
        )
    ).first()
    model = db.scalars(select(StrategyModel).where(StrategyModel.name == model_name)).first()
    if model is None or stat is None:
        return model.weight if model else Decimal("1.0")
    if not model.auto_adjust_weight:
        return model.weight

    current = model.weight
    new_weight = current

    if stat.sample_quality in ("INSUFFICIENT", "LOW"):
        # Don't punish yet - keep weight stable
        return current

    if stat.expectancy is not None and stat.expectancy < 0:
        new_weight = max(Decimal("0.3"), current - Decimal("0.1"))
    elif stat.profit_factor is not None and stat.profit_factor < Decimal("1.0"):
        new_weight = max(Decimal("0.3"), current - Decimal("0.1"))
    elif (
        stat.profit_factor is not None
        and stat.profit_factor > Decimal("1.5")
        and stat.expectancy is not None
        and stat.expectancy > 0
    ):
        new_weight = min(Decimal("1.0"), current + Decimal("0.05"))

    if new_weight != current:
        logger.info("model {} weight {} -> {}", model_name, current, new_weight)
        model.weight = new_weight
        db.commit()
    return new_weight


def update_all(db: Session, now: datetime | None = None) -> dict:
    now = now or utc_now()
    models = db.scalars(select(StrategyModel)).all()
    results: dict = {}
    for m in models:
        stats = update_stats_for_model(db, m.name, now)
        new_weight = adjust_weight(db, m.name, now)
        results[m.name] = {"stats": {k: v for k, v in stats.items()}, "weight": str(new_weight)}
    return results
