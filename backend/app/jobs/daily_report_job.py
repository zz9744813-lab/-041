"""Daily report job - takes a PortfolioSnapshot and emits stats.

V1 keeps it simple: snapshot equity = cash + sum(open positions market value);
no per-asset breakdown beyond US/crypto totals.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, select

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
        # Compute open positions exposure
        open_positions = list(db.scalars(select(Position).where(Position.status == "OPEN")).all())
        us_exposure = Decimal("0")
        crypto_exposure = Decimal("0")
        for p in open_positions:
            mkt_value = p.quantity * p.current_price
            trade = db.get(Trade, p.trade_id)
            if trade and trade.market == Market.US_STOCK.value:
                us_exposure += mkt_value
            elif trade:
                crypto_exposure += mkt_value
        market_value = us_exposure + crypto_exposure

        # Compute realized P&L history
        prev = db.scalars(
            select(PortfolioSnapshot)
            .order_by(desc(PortfolioSnapshot.timestamp))
            .limit(1)
        ).first()
        prev_equity = prev.equity if prev else settings.initial_capital_usd
        prev_cash = prev.cash if prev else settings.initial_capital_usd

        # Apply realized P&L from trades closed since last snapshot
        cutoff = prev.timestamp if prev else None
        stmt = select(Trade).where(Trade.status == "CLOSED")
        if cutoff is not None:
            stmt = stmt.where(Trade.exit_time > cutoff)
        closed_since = list(db.scalars(stmt).all())
        realized_delta = sum(
            (t.pnl_amount or Decimal("0") for t in closed_since), Decimal("0")
        )

        cash_now = prev_cash + realized_delta
        equity_now = cash_now + market_value

        # Drawdown
        all_eq = list(
            db.scalars(
                select(PortfolioSnapshot.equity).order_by(PortfolioSnapshot.timestamp)
            ).all()
        )
        peak = max(all_eq) if all_eq else equity_now
        peak = max(peak, equity_now)
        drawdown_pct = (peak - equity_now) / peak if peak > 0 else Decimal("0")

        # Total return pct vs initial capital
        total_return = (equity_now / settings.initial_capital_usd - Decimal("1")) if settings.initial_capital_usd else Decimal("0")

        # Daily P&L
        daily_pnl = equity_now - prev_equity

        # Consecutive losses: count from end of trades stream
        all_closed = list(
            db.scalars(
                select(Trade).where(Trade.status == "CLOSED").order_by(desc(Trade.exit_time))
            ).all()
        )
        consec = 0
        for t in all_closed:
            if t.exit_reason in ("STOP_LOSS", "AI_RISK_EXIT"):
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
            open_positions_count=len(open_positions),
            consecutive_losses=consec,
        )
        db.merge(snap)
        db.commit()
        return {
            "equity": str(equity_now),
            "cash": str(cash_now),
            "drawdown_pct": str(drawdown_pct),
            "open_positions": len(open_positions),
        }
    finally:
        db.close()
