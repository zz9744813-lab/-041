"""Paper trading engine per spec § 15.

Hard rules:
- fill_policy is fixed and explicit (spec § 8.3)
- Same bar SL+TP -> SL wins (conservative)
- Gap-down through SL -> fill at next_bar.open
- All time-related fns accept `now: datetime` for backtest reuse (spec § 22).
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Candle, Position, Signal, Trade
from app.models.enums import ExitReason, Market, TradeStatus
from app.services import data_service, risk_service
from app.utils.time_utils import utc_now


def _slippage_for(market: str) -> Decimal:
    s = get_settings()
    return s.slippage_us_stock if market == Market.US_STOCK.value else s.slippage_crypto


def _fee_for(market: str) -> Decimal:
    s = get_settings()
    return s.fee_us_stock if market == Market.US_STOCK.value else s.fee_crypto


def calculate_fill_price(signal: Signal, next_bar: Candle) -> Decimal | None:
    """Per spec § 15.3 / § 8.3.

    Returns None if the bar didn't fill the order (gap above range or never touched).
    """
    if signal.entry_low is None or signal.entry_high is None:
        return None

    el = signal.entry_low
    eh = signal.entry_high
    bar_open = next_bar.open

    # Scenario 1: open inside the entry range
    if el <= bar_open <= eh:
        return bar_open

    # Scenario 2: open above range (worse direction for LONG; we don't chase)
    if bar_open > eh:
        return None

    # Scenario 3: open below range, but bar reaches into range
    if bar_open < el and next_bar.high >= el:
        return el

    # Scenario 4: never touched
    return None


def _next_bar_after(db: Session, symbol: str, timeframe: str, after_ts: datetime) -> Candle | None:
    stmt = (
        select(Candle)
        .where(
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
            Candle.is_final.is_(True),
            Candle.timestamp > after_ts,
        )
        .order_by(Candle.timestamp.asc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def try_open_trade(
    db: Session, signal: Signal, now: datetime | None = None
) -> Trade | None:
    """Try to fill the signal at the next bar after the signal was created.

    Per spec § 15.2.
    """
    now = now or utc_now()

    # Re-check risk at fill time
    decision = risk_service.check(db, signal, now=now)
    if not decision.approved:
        signal.status = "REJECTED"
        signal.reject_reason = decision.reject_reason
        db.commit()
        return None

    last_bar = data_service.latest_final_bar(db, signal.symbol, "1h", now)
    if last_bar is None:
        signal.status = "APPROVED_WAITING_ENTRY"
        db.commit()
        return None
    next_bar = _next_bar_after(db, signal.symbol, "1h", last_bar.timestamp)
    if next_bar is None:
        # No bar after; keep waiting
        signal.status = "APPROVED_WAITING_ENTRY"
        db.commit()
        return None

    fill = calculate_fill_price(signal, next_bar)
    if fill is None:
        signal.status = "APPROVED_WAITING_ENTRY"
        db.commit()
        return None

    pct = decision.adjusted_position_size_pct or signal.position_size_pct or Decimal("0")
    state = risk_service.current_portfolio_state(db, now)
    position_value = state.equity * (pct / Decimal("100"))
    if position_value <= 0 or fill <= 0:
        signal.status = "REJECTED"
        signal.reject_reason = "zero_position_value"
        db.commit()
        return None
    quantity = position_value / fill

    # Slippage + fee
    slip = fill * _slippage_for(signal.market)
    fee = position_value * _fee_for(signal.market)
    fill_with_slip = fill + slip

    trade = Trade(
        signal_id=signal.id,
        symbol=signal.symbol,
        market=signal.market,
        direction=signal.direction,
        model_name=signal.model_name,
        entry_time=next_bar.timestamp,
        entry_price=fill_with_slip,
        entry_fill_policy="NEXT_BAR_OPEN_OR_TOUCH",
        quantity=quantity,
        position_value=fill_with_slip * quantity,
        slippage_paid=slip * quantity,
        fee_paid=fee,
        stop_loss_initial=signal.stop_loss,
        stop_loss_current=signal.stop_loss,
        target_1=signal.target_1,
        target_2=signal.target_2,
        max_holding_days=signal.expected_holding_days_max,
        status=TradeStatus.OPEN.value,
    )
    db.add(trade)
    db.flush()  # get trade.id

    position = Position(
        trade_id=trade.id,
        symbol=signal.symbol,
        quantity=quantity,
        avg_entry_price=fill_with_slip,
        current_price=fill_with_slip,
        stop_loss_current=signal.stop_loss,
        max_favorable_excursion=fill_with_slip,
        max_adverse_excursion=fill_with_slip,
    )
    db.add(position)
    signal.status = "EXECUTED"
    db.commit()
    db.refresh(trade)
    logger.info(
        "trade opened: {} qty={} entry={} sl={}",
        trade.symbol,
        quantity,
        fill_with_slip,
        signal.stop_loss,
    )
    return trade


def _close_trade(
    db: Session,
    trade: Trade,
    exit_price: Decimal,
    exit_time: datetime,
    exit_reason: str,
    exit_fill_policy: str = "DEFAULT",
) -> None:
    risk_per_share = trade.entry_price - trade.stop_loss_initial
    pnl_per_share = exit_price - trade.entry_price
    pnl_amount = pnl_per_share * trade.quantity - trade.fee_paid
    pnl_pct = (exit_price / trade.entry_price - Decimal("1")) if trade.entry_price else Decimal("0")
    r_multiple = (pnl_per_share / risk_per_share) if risk_per_share > 0 else Decimal("0")

    trade.exit_time = exit_time
    trade.exit_price = exit_price
    trade.exit_reason = exit_reason
    trade.exit_fill_policy = exit_fill_policy
    trade.pnl_amount = pnl_amount
    trade.pnl_pct = pnl_pct
    trade.realized_r_multiple = r_multiple
    trade.status = TradeStatus.CLOSED.value

    # Close the position
    pos = db.scalars(select(Position).where(Position.trade_id == trade.id)).first()
    if pos:
        pos.status = "CLOSED"
        pos.current_price = exit_price
        pos.unrealized_pnl = Decimal("0")

    db.commit()
    logger.info(
        "trade closed: {} exit={} reason={} pnl={} r={}",
        trade.symbol,
        exit_price,
        exit_reason,
        pnl_amount,
        r_multiple,
    )


def _update_trailing_stop(trade: Trade, bar: Candle) -> None:
    """Per spec § 15.5."""
    risk = trade.entry_price - trade.stop_loss_initial
    if risk <= 0:
        return
    floating_r = (bar.close - trade.entry_price) / risk
    if floating_r >= Decimal("3.0"):
        new_sl = trade.entry_price + risk
        if new_sl > trade.stop_loss_current:
            trade.stop_loss_current = new_sl
            trade.trailing_stop_activated = True
    elif floating_r >= Decimal("1.5"):
        new_sl = trade.entry_price
        if new_sl > trade.stop_loss_current:
            trade.stop_loss_current = new_sl
            trade.trailing_stop_activated = True


def update_position(
    db: Session, position: Position, now: datetime | None = None
) -> None:
    """Per spec § 15.4 - check SL/TP/trailing/max-holding for one open position."""
    now = now or utc_now()
    bar = data_service.latest_final_bar(db, position.symbol, "1h", now)
    if bar is None:
        return
    trade = db.get(Trade, position.trade_id)
    if trade is None or trade.status != TradeStatus.OPEN.value:
        return

    # Update floating P&L + MFE/MAE
    position.current_price = bar.close
    position.unrealized_pnl = (bar.close - trade.entry_price) * trade.quantity
    position.unrealized_pnl_pct = (bar.close / trade.entry_price - Decimal("1"))
    if bar.high > position.max_favorable_excursion:
        position.max_favorable_excursion = bar.high
    if bar.low < position.max_adverse_excursion or position.max_adverse_excursion == 0:
        position.max_adverse_excursion = bar.low
    position.holding_days = (now - trade.entry_time).days
    db.commit()

    sl = trade.stop_loss_current
    tp1 = trade.target_1
    tp2 = trade.target_2

    hit_sl = bar.low <= sl
    hit_tp1 = tp1 is not None and bar.high >= tp1
    hit_tp2 = tp2 is not None and bar.high >= tp2

    # Conflict: same-bar SL + TP -> SL wins (spec § 8.3)
    if hit_sl and (hit_tp1 or hit_tp2):
        _close_trade(db, trade, sl, bar.timestamp, ExitReason.STOP_LOSS.value,
                     "SL_PRIORITY_WHEN_CONFLICT")
        return

    # Gap-down through SL
    if bar.open <= sl:
        _close_trade(db, trade, bar.open, bar.timestamp, ExitReason.STOP_LOSS.value,
                     "GAP_DOWN_OPEN")
        return

    if hit_sl:
        _close_trade(db, trade, sl, bar.timestamp, ExitReason.STOP_LOSS.value)
        return

    if hit_tp2:
        _close_trade(db, trade, tp2, bar.timestamp, ExitReason.TAKE_PROFIT_2.value)
        return
    if hit_tp1:
        _close_trade(db, trade, tp1, bar.timestamp, ExitReason.TAKE_PROFIT_1.value)
        return

    _update_trailing_stop(trade, bar)
    db.commit()

    # Max holding
    if trade.max_holding_days and position.holding_days >= trade.max_holding_days:
        _close_trade(db, trade, bar.close, bar.timestamp, ExitReason.MAX_HOLDING.value)
        return


def manual_close(db: Session, trade: Trade, now: datetime | None = None) -> None:
    """Manually close a trade at the latest available bar's close."""
    now = now or utc_now()
    bar = data_service.latest_final_bar(db, trade.symbol, "1h", now)
    if bar is None:
        raise RuntimeError("No bar available to compute exit price")
    _close_trade(db, trade, bar.close, bar.timestamp, ExitReason.MANUAL.value, "MANUAL")


def update_all_open_positions(db: Session, now: datetime | None = None) -> dict:
    """Per spec § 15.4 - update every OPEN position; bulk-fetches Trade rows
    and latest 1h bars in two queries instead of 2N round-trips.
    """
    now = now or utc_now()
    positions = list(db.scalars(select(Position).where(Position.status == "OPEN")).all())
    if not positions:
        return {"checked": 0, "closed": 0}

    trade_ids = [p.trade_id for p in positions]
    symbols = list({p.symbol for p in positions})

    # Bulk Trade fetch
    trade_map: dict[int, Trade] = {
        t.id: t for t in db.scalars(select(Trade).where(Trade.id.in_(trade_ids))).all()
    }

    # Bulk latest-1h bar fetch (one GROUP BY per symbol).
    from sqlalchemy import func as _func, tuple_ as _tuple

    latest_per_symbol = (
        select(Candle.symbol, _func.max(Candle.timestamp).label("ts"))
        .where(
            Candle.symbol.in_(symbols),
            Candle.timeframe == "1h",
            Candle.is_final.is_(True),
            Candle.timestamp <= now,
        )
        .group_by(Candle.symbol)
        .subquery()
    )
    bar_stmt = (
        select(Candle)
        .join(
            latest_per_symbol,
            _tuple(Candle.symbol, Candle.timestamp)
            == _tuple(latest_per_symbol.c.symbol, latest_per_symbol.c.ts),
        )
        .where(Candle.timeframe == "1h", Candle.is_final.is_(True))
    )
    bar_map: dict[str, Candle] = {b.symbol: b for b in db.scalars(bar_stmt).all()}

    closed = 0
    for p in positions:
        bar = bar_map.get(p.symbol)
        trade = trade_map.get(p.trade_id)
        if bar is None or trade is None or trade.status != TradeStatus.OPEN.value:
            continue
        before = p.status
        _apply_position_update(db, p, trade, bar, now)
        if p.status != before:
            closed += 1
    return {"checked": len(positions), "closed": closed}


def _apply_position_update(
    db: Session, position: Position, trade: Trade, bar: Candle, now: datetime
) -> None:
    """Same logic as `update_position` but assumes Trade + bar are already loaded."""
    position.current_price = bar.close
    position.unrealized_pnl = (bar.close - trade.entry_price) * trade.quantity
    position.unrealized_pnl_pct = (bar.close / trade.entry_price - Decimal("1"))
    if bar.high > position.max_favorable_excursion:
        position.max_favorable_excursion = bar.high
    if bar.low < position.max_adverse_excursion or position.max_adverse_excursion == 0:
        position.max_adverse_excursion = bar.low
    position.holding_days = (now - trade.entry_time).days
    db.commit()

    sl = trade.stop_loss_current
    tp1 = trade.target_1
    tp2 = trade.target_2

    hit_sl = bar.low <= sl
    hit_tp1 = tp1 is not None and bar.high >= tp1
    hit_tp2 = tp2 is not None and bar.high >= tp2

    if hit_sl and (hit_tp1 or hit_tp2):
        _close_trade(db, trade, sl, bar.timestamp, ExitReason.STOP_LOSS.value,
                     "SL_PRIORITY_WHEN_CONFLICT")
        return
    if bar.open <= sl:
        _close_trade(db, trade, bar.open, bar.timestamp, ExitReason.STOP_LOSS.value,
                     "GAP_DOWN_OPEN")
        return
    if hit_sl:
        _close_trade(db, trade, sl, bar.timestamp, ExitReason.STOP_LOSS.value)
        return
    if hit_tp2:
        _close_trade(db, trade, tp2, bar.timestamp, ExitReason.TAKE_PROFIT_2.value)
        return
    if hit_tp1:
        _close_trade(db, trade, tp1, bar.timestamp, ExitReason.TAKE_PROFIT_1.value)
        return

    _update_trailing_stop(trade, bar)
    db.commit()

    if trade.max_holding_days and position.holding_days >= trade.max_holding_days:
        _close_trade(db, trade, bar.close, bar.timestamp, ExitReason.MAX_HOLDING.value)
        return
