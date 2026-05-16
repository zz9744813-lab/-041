"""Risk engine per spec § 14.

Hard rule: this engine has VETO power. Even if AI/strategy says go, if any check fails,
no trade.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import MarketRegime, PortfolioSnapshot, Position, Signal, Trade
from app.models.enums import Market, MarketRegimeEnum
from app.schemas.risk_schema import RiskDecision
from app.services import market_regime_service
from app.utils.time_utils import utc_now

# ---- Correlation groups per spec § 14.6 ----
CORRELATION_GROUPS: dict[str, set[str]] = {
    "US_TECH": {
        "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "AMD", "AVGO",
        "NFLX", "TSLA", "QQQ", "XLK", "SMH", "SOXX",
    },
    "US_BROAD": {"SPY", "DIA", "IWM"},
    "CRYPTO_BETA": {"BTC-USD", "ETH-USD", "COIN", "MSTR"},
    "AI_LEVERED": {"NVDA", "AMD", "SMH", "SOXX", "PLTR"},
}


@dataclass
class PortfolioState:
    equity: Decimal
    cash: Decimal
    us_stock_exposure: Decimal
    crypto_exposure: Decimal
    open_positions: list[Position]
    consecutive_losses: int
    max_drawdown_pct: Decimal


def current_portfolio_state(db: Session, now: datetime | None = None) -> PortfolioState:
    """Build a PortfolioState from latest snapshot + open positions.

    If no snapshot exists yet, fall back to initial capital.
    """
    now = now or utc_now()
    settings = get_settings()
    snap = db.scalars(
        select(PortfolioSnapshot)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .limit(1)
    ).first()

    open_positions = list(
        db.scalars(select(Position).where(Position.status == "OPEN")).all()
    )

    if snap:
        return PortfolioState(
            equity=snap.equity,
            cash=snap.cash,
            us_stock_exposure=snap.us_stock_exposure,
            crypto_exposure=snap.crypto_exposure,
            open_positions=open_positions,
            consecutive_losses=snap.consecutive_losses,
            max_drawdown_pct=snap.max_drawdown_pct,
        )
    # Bootstrap
    return PortfolioState(
        equity=settings.initial_capital_usd,
        cash=settings.initial_capital_usd,
        us_stock_exposure=Decimal("0"),
        crypto_exposure=Decimal("0"),
        open_positions=[],
        consecutive_losses=0,
        max_drawdown_pct=Decimal("0"),
    )


def _market_value(position: Position) -> Decimal:
    return position.quantity * position.current_price


def check(db: Session, signal: Signal, now: datetime | None = None) -> RiskDecision:
    """Run all 13 checks per spec § 14.2.

    Short-circuit: any failure returns approved=False with reject_reason.
    """
    now = now or utc_now()
    settings = get_settings()
    state = current_portfolio_state(db, now)
    triggered: list[str] = []
    warnings: list[str] = []

    # 1. confidence
    if signal.confidence_score < settings.min_confidence:
        return RiskDecision(
            approved=False,
            reject_reason=f"confidence {signal.confidence_score} < {settings.min_confidence}",
            triggered_rules=["min_confidence"],
        )

    # 2. risk-reward ratio
    rr = signal.risk_reward_ratio
    if rr is not None and rr < settings.min_rr:
        return RiskDecision(
            approved=False,
            reject_reason=f"R/R {rr} < {settings.min_rr}",
            triggered_rules=["min_rr"],
        )

    # 3. per-trade risk (only if LONG with prices)
    if signal.entry_low and signal.stop_loss and signal.position_size_pct:
        risk_per_share = signal.entry_low - signal.stop_loss
        if risk_per_share <= 0:
            return RiskDecision(
                approved=False,
                reject_reason="entry <= stop_loss",
                triggered_rules=["bad_stop_loss"],
            )
        risk_pct = (risk_per_share / signal.entry_low) * (signal.position_size_pct / Decimal("100"))
        if risk_pct > settings.max_per_trade_risk_pct:
            return RiskDecision(
                approved=False,
                reject_reason=f"per_trade_risk {risk_pct:.4f} > {settings.max_per_trade_risk_pct}",
                triggered_rules=["max_per_trade_risk"],
            )

    # Get regime-based limits
    regime_row = db.scalars(
        select(MarketRegime).order_by(MarketRegime.timestamp.desc()).limit(1)
    ).first()
    regime_name = regime_row.regime if regime_row else None
    limits = market_regime_service.limits_for(regime_name)

    # 12. regime allows new opens
    if not limits["allow_new"]:
        return RiskDecision(
            approved=False,
            reject_reason=f"regime {regime_name} forbids new opens",
            triggered_rules=["regime_no_new_opens"],
        )

    intended_pct = signal.position_size_pct or Decimal("0")
    intended_value = state.equity * (intended_pct / Decimal("100"))

    # 4. per-asset cap
    same_symbol_value = sum(
        (_market_value(p) for p in state.open_positions if p.symbol == signal.symbol),
        Decimal("0"),
    )
    if (same_symbol_value + intended_value) / max(state.equity, Decimal("1")) > settings.max_per_asset_pct:
        return RiskDecision(
            approved=False,
            reject_reason=f"per-asset cap exceeded for {signal.symbol}",
            triggered_rules=["max_per_asset"],
        )

    # 5. US stock total cap (regime-adjusted)
    if signal.market == Market.US_STOCK.value:
        cap = limits["max_total_pct"]  # using total cap as proxy for US cap in V1
        if (state.us_stock_exposure + intended_value) / max(state.equity, Decimal("1")) > cap:
            return RiskDecision(
                approved=False,
                reject_reason=f"US stock cap {cap} exceeded",
                triggered_rules=["max_us_stock"],
            )

    # 6. crypto cap
    if signal.market == Market.CRYPTO.value:
        if (state.crypto_exposure + intended_value) / max(state.equity, Decimal("1")) > settings.max_crypto_pct:
            return RiskDecision(
                approved=False,
                reject_reason=f"crypto cap {settings.max_crypto_pct} exceeded",
                triggered_rules=["max_crypto"],
            )

    # 7. total cap
    total_value = state.us_stock_exposure + state.crypto_exposure
    if (total_value + intended_value) / max(state.equity, Decimal("1")) > limits["max_total_pct"]:
        return RiskDecision(
            approved=False,
            reject_reason=f"total cap {limits['max_total_pct']} exceeded",
            triggered_rules=["max_total"],
        )

    # 8. min cash reserve
    cash_after = state.cash - intended_value
    if cash_after / max(state.equity, Decimal("1")) < settings.min_cash_reserve_pct:
        return RiskDecision(
            approved=False,
            reject_reason=f"cash reserve below {settings.min_cash_reserve_pct}",
            triggered_rules=["min_cash_reserve"],
        )

    # 9 + 10. consecutive losses + drawdown
    cl = state.consecutive_losses
    dd = state.max_drawdown_pct
    adjusted_pct = intended_pct
    if cl >= 5:
        return RiskDecision(
            approved=False,
            reject_reason=f"consecutive_losses={cl} - paused 48h",
            triggered_rules=["paused_consecutive_losses"],
        )
    if cl >= 3:
        adjusted_pct = adjusted_pct * Decimal("0.5")
        warnings.append("consecutive_losses>=3, halving size")
        triggered.append("size_halved_losses")

    if dd >= Decimal("0.10"):
        return RiskDecision(
            approved=False,
            reject_reason=f"drawdown {dd} >= 10% - manual review required",
            triggered_rules=["drawdown_severe"],
        )
    if dd >= Decimal("0.08"):
        return RiskDecision(
            approved=False,
            reject_reason=f"drawdown {dd} >= 8% - new opens halted",
            triggered_rules=["drawdown_halt"],
        )
    if dd >= Decimal("0.05"):
        adjusted_pct = adjusted_pct * Decimal("0.7")
        warnings.append(f"drawdown {dd} >= 5%, sizing 70%")
        triggered.append("size_reduced_drawdown")

    # 11. existing same-direction position on same symbol
    existing = next(
        (p for p in state.open_positions if p.symbol == signal.symbol),
        None,
    )
    if existing:
        return RiskDecision(
            approved=False,
            reject_reason=f"existing OPEN position on {signal.symbol}",
            triggered_rules=["already_in_position"],
        )

    # 13. correlation groups (spec § 14.6)
    for group_name, members in CORRELATION_GROUPS.items():
        if signal.symbol not in members:
            continue
        group_value = sum(
            (_market_value(p) for p in state.open_positions if p.symbol in members),
            Decimal("0"),
        )
        if (group_value + intended_value) / max(state.equity, Decimal("1")) > settings.max_per_correlation_group_pct:
            return RiskDecision(
                approved=False,
                reject_reason=f"correlation group {group_name} cap exceeded",
                triggered_rules=[f"corr_group_{group_name}"],
            )

    # All checks passed
    return RiskDecision(
        approved=True,
        adjusted_position_size_pct=adjusted_pct if adjusted_pct != intended_pct else None,
        warnings=warnings,
        triggered_rules=triggered,
    )


def re_filter_pending(db: Session, now: datetime | None = None) -> dict:
    """Per spec § 14.7 - re-run risk on all APPROVED_WAITING_ENTRY signals.

    Expire ones whose valid_until has passed; reject ones that no longer pass risk.
    """
    now = now or utc_now()
    pending = db.scalars(
        select(Signal).where(Signal.status == "APPROVED_WAITING_ENTRY")
    ).all()
    expired = 0
    rejected = 0
    kept = 0
    for sig in pending:
        if sig.valid_until <= now:
            sig.status = "EXPIRED"
            expired += 1
            continue
        decision = check(db, sig, now)
        if not decision.approved:
            sig.status = "REJECTED"
            sig.reject_reason = f"Re-filter: {decision.reject_reason}"
            rejected += 1
        else:
            kept += 1
    db.commit()
    return {"expired": expired, "rejected": rejected, "kept": kept}
