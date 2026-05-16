"""Decision service per spec § 17 - generates SignalPlan via LLM or rule fallback.

Layout:
- generate_signal_plan_rule_based(): pure rules from StrategyScore -> SignalPlan
- generate_signal_plan_llm(): LLM-driven, with input_hash cache and degradation
- The job calls generate(): if ENABLE_LLM_DECISION, try LLM; on fail, fall back to rules.
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Candle, IndicatorSnapshot, MarketRegime
from app.models.enums import (
    Direction,
    Market,
    SignalStatus,
    SignalType,
)
from app.schemas.signal_schema import SignalPlan, SignalPlanInput
from app.services import llm_client
from app.strategies.base import StrategyInput, StrategyScore
from app.utils.time_utils import utc_now


SIGNAL_GEN_SYSTEM_PROMPT = """\
你是一个保守的量化交易研究员。你只输出严格符合 SignalPlan JSON Schema 的结构化交易计划。

不允许输出 Markdown、解释段落、免责声明。

规则:
1. 如果数据不足、市场环境混乱或无法形成高概率判断,必须输出
   signal_type="NO_TRADE" 或 "INSUFFICIENT_DATA",direction="WATCH"。
   不要硬编一个低 confidence 的 LONG。
2. 所有点位必须在 current_price 的合理范围内(止损不超过 current 的 10%)。
3. invalid_condition 字段必填且非空,描述什么情况下应放弃该计划。
4. 风险收益比 < 1.5 的计划应输出为 NO_TRADE。
5. 不要追高: entry_high 不应高于 current_price * 1.03。

只输出严格 JSON,无任何额外文本。
"""


def _decay_hours(market: str) -> int:
    s = get_settings()
    return s.default_signal_decay_hours_us_stock if market == Market.US_STOCK.value else s.default_signal_decay_hours_crypto


def generate_signal_plan_rule_based(
    score: StrategyScore,
    market: str,
    current_price: Decimal,
) -> SignalPlan:
    """Convert a StrategyScore into a SignalPlan using pure rules."""
    if score.suggested_action == "ENTER" and score.entry_low and score.stop_loss and score.target_1:
        # Compute rr
        risk = score.entry_low - score.stop_loss
        rr = (
            (score.target_1 - score.entry_high) / risk
            if (risk > 0 and score.entry_high)
            else Decimal("0")
        )
        # Position size: scale with confidence
        confidence = max(60, min(95, score.final_score))
        # Map score to risk pct: aim for ~1% risk regardless of score size
        # position_size_pct s.t. (entry-stop)/entry * pct = MAX_RISK
        risk_pct_of_price = (score.entry_low - score.stop_loss) / score.entry_low
        target_position_risk = Decimal("0.01")  # 1% portfolio
        position_size_pct = (target_position_risk / risk_pct_of_price) * Decimal("100")
        position_size_pct = min(Decimal("15"), position_size_pct)

        signal_type = SignalType.PULLBACK_BUY
        if score.model_name == "trend_breakout":
            signal_type = SignalType.TREND_BREAKOUT
        elif score.model_name == "ma_trend":
            signal_type = SignalType.TREND_FOLLOW

        return SignalPlan(
            symbol=score.symbol,
            market=Market(market),
            direction=Direction.LONG,
            signal_type=signal_type,
            current_price=current_price,
            entry_low=score.entry_low,
            entry_high=score.entry_high,
            stop_loss=score.stop_loss,
            target_1=score.target_1,
            target_2=score.target_2,
            confidence_score=confidence,
            risk_reward_ratio=rr.quantize(Decimal("0.0001")),
            position_size_pct=position_size_pct.quantize(Decimal("0.01")),
            expected_holding_days_min=3,
            expected_holding_days_max=20,
            signal_decay_hours=_decay_hours(market),
            reason=f"[rule-based] {score.raw_reason}",
            risk_note=f"stop {score.stop_loss}, target {score.target_1}",
            invalid_condition=f"close below {score.stop_loss}",
            follow_up_rule="trail to entry at +1.5R",
        )
    # WATCH fallback
    return SignalPlan(
        symbol=score.symbol,
        market=Market(market),
        direction=Direction.WATCH,
        signal_type=SignalType.NO_TRADE,
        current_price=current_price,
        confidence_score=max(0, min(60, score.final_score)),
        reason=f"[rule-based] no entry: {score.raw_reason or 'low score'}",
        risk_note="",
        invalid_condition="when setup conditions emerge",
    )


def generate_signal_plan_llm(
    db: Session,
    score: StrategyScore,
    market: str,
    current_price: Decimal,
    market_regime_name: str | None,
    daily_summary: dict,
    four_hour_summary: dict,
    one_hour_summary: dict,
    portfolio_context: dict,
    now: datetime | None = None,
) -> tuple[SignalPlan | None, str]:
    """Call LLM. Returns (plan, source) where source is 'llm' or 'cache'.

    On any failure returns (None, 'failed')."""
    settings = get_settings()
    if not settings.enable_llm_decision:
        return None, "disabled"

    constraints = {
        "min_rr": float(settings.min_rr),
        "max_position_size_pct": 15,
        "max_per_trade_risk_pct": float(settings.max_per_trade_risk_pct * 100),
    }
    payload = SignalPlanInput(
        symbol=score.symbol,
        market=Market(market),
        current_price=current_price,
        market_regime=market_regime_name or "UNKNOWN",
        daily=daily_summary,
        four_hour=four_hour_summary,
        one_hour=one_hour_summary,
        strategy_scores={score.model_name: {"final_score": score.final_score}},
        portfolio_context=portfolio_context,
        constraints=constraints,
        asof_timestamp=now or utc_now(),
    )

    parsed, log = llm_client.call_llm_structured(
        db,
        purpose="signal_generation",
        system_prompt=SIGNAL_GEN_SYSTEM_PROMPT,
        user_input=payload,
        prompt_version=settings.prompt_version,
        schema=SignalPlan,
    )
    if parsed is None:
        logger.warning("LLM signal failed: {}", log.error_message)
        return None, "failed"
    source = "cache" if log.cached else "llm"
    return parsed, source
