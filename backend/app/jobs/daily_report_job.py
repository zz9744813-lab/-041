"""Daily report job - takes a PortfolioSnapshot and emits stats.

V1 keeps it simple: snapshot equity = cash + sum(open positions market value);
no per-asset breakdown beyond US/crypto totals.

v2.1: removed N+1 (`db.get(Trade)` per position) and the full equity-history
scan; now uses one JOIN + `func.max` for peak equity.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select

from app.config import get_settings
from app.database import SessionLocal
from app.jobs._helpers import with_health_record
from app.models import PortfolioSnapshot, Position, Trade
from app.models.enums import Market
from app.utils.time_utils import utc_now


@with_health_record("daily_report")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        settings = get_settings()
        # Open positions + their Trade in one query
        rows = list(
            db.execute(
                select(Position, Trade).join(Trade, Trade.id == Position.trade_id)
                .where(Position.status == "OPEN")
            ).all()
        )
        us_exposure = Decimal("0")
        crypto_exposure = Decimal("0")
        for p, trade in rows:
            mkt_value = p.quantity * p.current_price
            if trade.market == Market.US_STOCK.value:
                us_exposure += mkt_value
            else:
                crypto_exposure += mkt_value
        market_value = us_exposure + crypto_exposure

        prev = db.scalars(
            select(PortfolioSnapshot)
            .order_by(desc(PortfolioSnapshot.timestamp))
            .limit(1)
        ).first()
        prev_equity = prev.equity if prev else settings.initial_capital_usd
        prev_cash = prev.cash if prev else settings.initial_capital_usd

        # Apply realized P&L from trades closed since last snapshot
        cutoff = prev.timestamp if prev else None
        stmt = select(Trade.pnl_amount).where(Trade.status == "CLOSED")
        if cutoff is not None:
            stmt = stmt.where(Trade.exit_time > cutoff)
        realized_delta = sum(
            (v or Decimal("0") for v in db.scalars(stmt).all()), Decimal("0")
        )

        cash_now = prev_cash + realized_delta
        equity_now = cash_now + market_value

        # Drawdown - server-side max instead of pulling the entire history.
        peak = (
            db.scalar(select(func.max(PortfolioSnapshot.equity)))
            or equity_now
        )
        peak = max(peak, equity_now)
        drawdown_pct = (peak - equity_now) / peak if peak > 0 else Decimal("0")

        total_return = (
            equity_now / settings.initial_capital_usd - Decimal("1")
            if settings.initial_capital_usd
            else Decimal("0")
        )

        daily_pnl = equity_now - prev_equity

        # Consecutive losses: only fetch exit_reason col, not whole rows.
        consec = 0
        for reason in db.scalars(
            select(Trade.exit_reason)
            .where(Trade.status == "CLOSED")
            .order_by(desc(Trade.exit_time))
        ).all():
            if reason in ("STOP_LOSS", "AI_RISK_EXIT"):
                consec += 1
            else:
                break

        snap = PortfolioSnapshot(
            timestamp=now.replace(microsecond=0),
            cash=cash_now,
            equity=equity_now,
            market_value=market_value,
            us_stock_exposure=us_exposure,
            crypto_exposure=crypto_exposure,
            daily_pnl=daily_pnl,
            total_return_pct=total_return,
            max_drawdown_pct=drawdown_pct,
            open_positions_count=len(rows),
            consecutive_losses=consec,
        )
        db.merge(snap)
        db.commit()
        return {
            "equity": str(equity_now),
            "cash": str(cash_now),
            "drawdown_pct": str(drawdown_pct),
            "open_positions": len(rows),
        }
    finally:
        db.close()
