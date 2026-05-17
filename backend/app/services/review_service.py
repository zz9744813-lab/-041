"""Narration service per spec § 17.5-17.7 - LLM-driven trade reviews."""
from datetime import datetime
from decimal import Decimal

from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Position, Review, Trade
from app.services import llm_client
from app.utils.time_utils import utc_now


class ReviewOutput(BaseModel):
    schema_version: str = "1.0"
    summary: str = Field(min_length=1, max_length=4000)
    entry_quality: int = Field(ge=1, le=5)
    exit_quality: int = Field(ge=1, le=5)
    risk_control_quality: int = Field(ge=1, le=5)
    what_worked: list[str] = []
    what_failed: list[str] = []
    model_adjustment_suggestion: str = ""
    should_keep_model_signal: bool = True


REVIEW_SYSTEM_PROMPT = """\
你是一位严肃的交易复盘师。给你一笔已平仓的交易,请用中文写一份简短复盘:

要求:
- 输出严格 JSON,符合 ReviewOutput schema。
- summary 不超过 800 字。
- entry_quality / exit_quality / risk_control_quality 都是 1-5 整数。
- what_worked / what_failed 各列出 0-5 条。
- model_adjustment_suggestion 给出对该策略模型的具体建议(如"R/R 太低,提高门槛到 2")。
- should_keep_model_signal: 这次失败/成功是否说明该策略仍值得保留。
"""


def _build_input(trade: Trade, position: Position | None) -> dict:
    return {
        "symbol": trade.symbol,
        "model_name": trade.model_name,
        "trade_summary": {
            "entry_time": trade.entry_time.isoformat(),
            "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
            "entry_price": str(trade.entry_price),
            "exit_price": str(trade.exit_price) if trade.exit_price else None,
            "exit_reason": trade.exit_reason,
            "pnl_amount": str(trade.pnl_amount) if trade.pnl_amount else None,
            "pnl_pct": str(trade.pnl_pct) if trade.pnl_pct else None,
            "r_multiple": str(trade.realized_r_multiple) if trade.realized_r_multiple else None,
        },
        "during_trade": {
            "max_favorable_excursion": str(position.max_favorable_excursion) if position else None,
            "max_adverse_excursion": str(position.max_adverse_excursion) if position else None,
            "holding_days": position.holding_days if position else None,
        },
    }


def _rule_based_review(trade: Trade) -> ReviewOutput:
    """Fallback when LLM is disabled or unavailable."""
    pnl = float(trade.pnl_amount or 0)
    r = float(trade.realized_r_multiple or 0)
    won = pnl > 0
    quality = 4 if won else 2
    summary = (
        f"{trade.symbol} {trade.exit_reason} closed at {trade.exit_price}. "
        f"P&L {pnl:.2f} ({r:.2f}R)."
    )
    return ReviewOutput(
        summary=summary,
        entry_quality=3,
        exit_quality=quality,
        risk_control_quality=4,
        what_worked=["pre-set stop loss honored"] if won else [],
        what_failed=[] if won else ["entry too aggressive or stop too tight"],
        model_adjustment_suggestion="",
        should_keep_model_signal=True,
    )


def generate_for_trade(db: Session, trade_id: int, now: datetime | None = None) -> Review:
    """Generate (or regenerate) a Review for a closed trade."""
    now = now or utc_now()
    trade = db.get(Trade, trade_id)
    if trade is None:
        raise ValueError(f"trade {trade_id} not found")
    if trade.status != "CLOSED":
        raise ValueError(f"trade {trade_id} is {trade.status}, cannot review")
    pos = db.scalars(select(Position).where(Position.trade_id == trade_id)).first()

    settings = get_settings()
    review_data: ReviewOutput
    cost: Decimal | None = None
    provider: str | None = None
    model: str | None = None
    llm_call_log_id: int | None = None

    if settings.anthropic_api_key or settings.openai_api_key:
        parsed, log = llm_client.call_llm_structured(
            db,
            purpose="review",
            system_prompt=REVIEW_SYSTEM_PROMPT,
            user_input=_build_input(trade, pos),
            prompt_version=settings.prompt_version,
            schema=ReviewOutput,
            model_override=settings.narration_model,
            now=now,
        )
        if parsed is not None:
            review_data = parsed
            cost = log.cost_usd
            provider = log.provider
            model = log.model
            llm_call_log_id = log.id
        else:
            logger.warning("review LLM failed; falling back to rule-based")
            review_data = _rule_based_review(trade)
    else:
        review_data = _rule_based_review(trade)

    # Upsert one review per trade
    existing = db.scalars(select(Review).where(Review.trade_id == trade_id)).first()
    if existing:
        existing.summary = review_data.summary
        existing.entry_quality = review_data.entry_quality
        existing.exit_quality = review_data.exit_quality
        existing.risk_control_quality = review_data.risk_control_quality
        existing.what_worked = review_data.what_worked
        existing.what_failed = review_data.what_failed
        existing.model_adjustment_suggestion = review_data.model_adjustment_suggestion
        existing.should_keep_model_signal = review_data.should_keep_model_signal
        existing.llm_provider = provider
        existing.llm_model = model
        existing.llm_cost_usd = cost
        existing.llm_call_log_id = llm_call_log_id
        return existing

    review = Review(
        trade_id=trade_id,
        summary=review_data.summary,
        entry_quality=review_data.entry_quality,
        exit_quality=review_data.exit_quality,
        risk_control_quality=review_data.risk_control_quality,
        what_worked=review_data.what_worked,
        what_failed=review_data.what_failed,
        model_adjustment_suggestion=review_data.model_adjustment_suggestion,
        should_keep_model_signal=review_data.should_keep_model_signal,
        llm_provider=provider,
        llm_model=model,
        llm_cost_usd=cost,
        llm_call_log_id=llm_call_log_id,
    )
    db.add(review)
    return review
