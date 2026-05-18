"""Generate signals job - end-to-end pipeline.

Per spec § 20.1:
1. For each active asset
2. Pull latest closed candles + indicators
3. Run all 3 strategies, pick the highest-weighted one (AI Composite)
4. Threshold gate (final_score >= 65)
5. Build SignalPlan via LLM (if enabled) or rule-based
6. Validate via Pydantic
7. Run risk check
8. Try to open trade if approved + price in range
9. Otherwise mark APPROVED_WAITING_ENTRY

v2.1: persists `strategy_score` on each Signal and writes a SignalSkip row
for every symbol where the LLM was NOT invoked, so the user can see why
nothing happened from the UI instead of digging through scheduler logs.
"""
import dataclasses
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.jobs._helpers import with_health_record
from app.models import (
    Asset,
    Candle,
    IndicatorSnapshot,
    MarketRegime,
    Signal,
    SignalSkip,
)
from app.models.enums import Market, SignalStatus
from app.schemas.signal_schema import SignalPlan
from app.services import (
    data_service,
    decision_service,
    indicator_service,
    paper_trading_service,
    risk_service,
)
from app.strategies import ALL_STRATEGIES, combine
from app.strategies.base import StrategyInput, StrategyScore
from app.utils.time_utils import utc_now


def _build_summary(ind: IndicatorSnapshot | None, candle: Candle | None) -> dict:
    if ind is None or candle is None:
        return {}
    close = float(candle.close)
    return {
        "close": close,
        "ma20": float(ind.ma20) if ind.ma20 else None,
        "ma50": float(ind.ma50) if ind.ma50 else None,
        "ma200": float(ind.ma200) if ind.ma200 else None,
        "rsi14": float(ind.rsi14) if ind.rsi14 else None,
        "macd_hist": float(ind.macd_hist) if ind.macd_hist else None,
        "atr14_pct": float(ind.atr14_pct) if ind.atr14_pct else None,
        "support": float(ind.support_level) if ind.support_level else None,
        "resistance": float(ind.resistance_level) if ind.resistance_level else None,
        "above_ma20": close > float(ind.ma20) if ind.ma20 else None,
        "above_ma50": close > float(ind.ma50) if ind.ma50 else None,
        "above_ma200": close > float(ind.ma200) if ind.ma200 else None,
    }


def _strategy_score_to_dict(s: StrategyScore) -> dict:
    """Convert StrategyScore dataclass to a JSON-safe dict for persistence."""
    d = dataclasses.asdict(s)
    # Decimal values come from rule-based scoring; stringify them
    for k, v in list(d.items()):
        if isinstance(v, Decimal):
            d[k] = str(v)
    return d


def _record_skip(
    db: Session,
    batch_id: str,
    symbol: str,
    reason: str,
    detail: str | None = None,
    score: int | None = None,
    model_name: str | None = None,
) -> None:
    skip = SignalSkip(
        batch_id=batch_id,
        symbol=symbol,
        reason=reason,
        detail=detail,
        score=score,
        model_name=model_name,
    )
    db.add(skip)


def _persist_signal(
    db: Session,
    plan: SignalPlan,
    model_name: str,
    input_hash: str,
    batch_id: str,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_call_log_id: int | None = None,
    strategy_score: dict | None = None,
    now: datetime | None = None,
) -> Signal:
    now = now or utc_now()
    settings = get_settings()
    decay_hours = plan.signal_decay_hours or (
        settings.default_signal_decay_hours_us_stock
        if plan.market.value == Market.US_STOCK.value
        else settings.default_signal_decay_hours_crypto
    )
    valid_until = now + timedelta(hours=decay_hours)

    sig = Signal(
        symbol=plan.symbol,
        market=plan.market.value,
        direction=plan.direction.value,
        signal_type=plan.signal_type.value,
        schema_version=plan.schema_version,
        current_price=plan.current_price,
        entry_low=plan.entry_low,
        entry_high=plan.entry_high,
        stop_loss=plan.stop_loss,
        target_1=plan.target_1,
        target_2=plan.target_2,
        confidence_score=plan.confidence_score,
        risk_reward_ratio=plan.risk_reward_ratio,
        position_size_pct=plan.position_size_pct,
        expected_holding_days_min=plan.expected_holding_days_min,
        expected_holding_days_max=plan.expected_holding_days_max,
        signal_decay_hours=decay_hours,
        model_name=model_name,
        reason=plan.reason,
        risk_note=plan.risk_note,
        invalid_condition=plan.invalid_condition,
        follow_up_rule=plan.follow_up_rule,
        strategy_score=strategy_score,
        input_hash=input_hash,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_call_log_id=llm_call_log_id,
        prompt_version=settings.prompt_version,
        status=SignalStatus.NEW.value,
        valid_until=valid_until,
        generation_batch_id=batch_id,
    )
    db.add(sig)
    db.flush()
    return sig


def _supersede_pending(db: Session, symbol: str, direction: str, current_id: int) -> int:
    """Per spec § 8.4: same-symbol same-direction new signal supersedes pending older ones."""
    stmt = select(Signal).where(
        Signal.symbol == symbol,
        Signal.direction == direction,
        Signal.status == SignalStatus.APPROVED_WAITING_ENTRY.value,
        Signal.id != current_id,
    )
    n = 0
    for old in db.scalars(stmt).all():
        old.status = SignalStatus.SUPERSEDED.value
        n += 1
    return n


def _process_one_asset(
    db: Session,
    asset: Asset,
    regime: MarketRegime | None,
    batch_id: str,
    now: datetime,
) -> dict:
    settings = get_settings()
    candles_1d = data_service.candles_until(db, asset.symbol, "1d", now, limit=300)
    candles_4h = data_service.candles_until(db, asset.symbol, "4h", now, limit=300)
    candles_1h = data_service.candles_until(db, asset.symbol, "1h", now, limit=300)
    if not candles_1d:
        _record_skip(db, batch_id, asset.symbol, "no_1d_candles")
        return {"symbol": asset.symbol, "skipped": "no_1d_candles"}

    ind_1d = indicator_service.latest_snapshot(db, asset.symbol, "1d", now)
    ind_4h = indicator_service.latest_snapshot(db, asset.symbol, "4h", now)
    ind_1h = indicator_service.latest_snapshot(db, asset.symbol, "1h", now)

    si = StrategyInput(
        asset=asset,
        latest_candles_1d=candles_1d,
        latest_candles_4h=candles_4h,
        latest_candles_1h=candles_1h,
        indicators_1d=ind_1d,
        indicators_4h=ind_4h,
        indicators_1h=ind_1h,
        market_regime=regime,
        now=now,
    )

    sub_scores = [s.score(si) for s in ALL_STRATEGIES]
    composite = combine(db, si, sub_scores)
    if not composite.best_score:
        _record_skip(db, batch_id, asset.symbol, "no_strategy_score")
        return {"symbol": asset.symbol, "skipped": "no_strategy_score"}

    best = composite.best_score
    if best.final_score < settings.strategy_score_threshold:
        _record_skip(
            db, batch_id, asset.symbol, "below_threshold",
            detail=best.raw_reason,
            score=best.final_score, model_name=best.model_name,
        )
        return {
            "symbol": asset.symbol,
            "best_model": best.model_name,
            "score": best.final_score,
            "skipped": "below_threshold",
        }

    current_price = candles_1d[-1].close
    plan: SignalPlan | None = None
    source = "rule"
    llm_provider = None
    llm_model = None
    llm_call_log_id: int | None = None

    if settings.enable_llm_decision:
        portfolio_ctx = {
            "has_open_position": any(
                p.symbol == asset.symbol
                for p in risk_service.current_portfolio_state(db, now).open_positions
            ),
        }
        plan_llm, src, log_id = decision_service.generate_signal_plan_llm(
            db,
            best,
            asset.market,
            current_price,
            regime.regime if regime else None,
            _build_summary(ind_1d, candles_1d[-1] if candles_1d else None),
            _build_summary(ind_4h, candles_4h[-1] if candles_4h else None),
            _build_summary(ind_1h, candles_1h[-1] if candles_1h else None),
            portfolio_ctx,
            now=now,
        )
        if plan_llm:
            plan = plan_llm
            source = src
            llm_provider = settings.llm_provider
            llm_model = settings.decision_model
            llm_call_log_id = log_id

    if plan is None:
        plan = decision_service.generate_signal_plan_rule_based(
            best, asset.market, current_price
        )
        source = "rule_fallback" if settings.enable_llm_decision else "rule"

    from app.services.llm_client import compute_input_hash
    input_hash = compute_input_hash(
        plan.model_dump(mode="json"), settings.prompt_version
    )

    sig = _persist_signal(
        db, plan, best.model_name, input_hash, batch_id,
        llm_provider=llm_provider, llm_model=llm_model,
        llm_call_log_id=llm_call_log_id,
        strategy_score=_strategy_score_to_dict(best),
        now=now,
    )

    decision = risk_service.check(db, sig, now=now)
    if not decision.approved:
        sig.status = SignalStatus.REJECTED.value
        sig.reject_reason = decision.reject_reason
        db.commit()
        return {
            "symbol": asset.symbol,
            "model": best.model_name,
            "source": source,
            "rejected": decision.reject_reason,
        }

    sig.status = SignalStatus.APPROVED.value
    if decision.adjusted_position_size_pct is not None:
        sig.position_size_pct = decision.adjusted_position_size_pct
    superseded = _supersede_pending(db, sig.symbol, sig.direction, sig.id)
    db.commit()

    trade = paper_trading_service.try_open_trade(db, sig, now=now)

    return {
        "symbol": asset.symbol,
        "model": best.model_name,
        "score": best.final_score,
        "source": source,
        "trade_id": trade.id if trade else None,
        "status": sig.status,
        "superseded_pending": superseded,
    }


@with_health_record("generate_signals")
def run(now: datetime | None = None) -> dict:
    return run_streaming(now=now)


def run_streaming(
    now: datetime | None = None,
    on_event: Callable[[dict], None] | None = None,
) -> dict:
    now = now or utc_now()
    db = SessionLocal()

    def _emit(event: dict) -> None:
        if on_event is None:
            return
        try:
            on_event(event)
        except Exception:
            logger.exception("on_event callback raised")

    try:
        rf = risk_service.re_filter_pending(db, now)

        regime = db.scalars(
            select(MarketRegime).order_by(MarketRegime.timestamp.desc()).limit(1)
        ).first()
        batch_id = str(uuid.uuid4())
        results = []
        assets = db.scalars(select(Asset).where(Asset.is_active.is_(True))).all()
        _emit({"type": "asset_total", "total": len(assets), "batch_id": batch_id})
        for asset in assets:
            _emit({"type": "asset_start", "symbol": asset.symbol})
            try:
                r = _process_one_asset(db, asset, regime, batch_id, now)
                # Commit any SignalSkip rows recorded during this asset.
                db.commit()
                results.append(r)
                _emit({"type": "asset_done", "symbol": asset.symbol, "result": r})
            except Exception as e:
                db.rollback()
                logger.exception("signal gen failed for {}", asset.symbol)
                err = {"symbol": asset.symbol, "error": str(e)}
                results.append(err)
                _emit({"type": "asset_error", "symbol": asset.symbol, "error": str(e)})
        return {
            "batch_id": batch_id,
            "regime": regime.regime if regime else None,
            "re_filter": rf,
            "results": results,
        }
    finally:
        db.close()
