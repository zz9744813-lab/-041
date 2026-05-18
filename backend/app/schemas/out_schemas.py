"""Pydantic out schemas - ensure JSON serialization is complete + typed.

Used as response_model in FastAPI routes so dates / Decimals / enums always
serialize cleanly to JSON the frontend can consume.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CandleOut(_Base):
    symbol: str
    timeframe: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    adjustment: str
    is_final: bool


class IndicatorSnapshotOut(_Base):
    symbol: str
    timeframe: str
    timestamp: datetime
    based_on_closed_bar: bool
    ma20: Decimal | None = None
    ma50: Decimal | None = None
    ma200: Decimal | None = None
    ema20: Decimal | None = None
    ema50: Decimal | None = None
    rsi14: Decimal | None = None
    macd: Decimal | None = None
    macd_signal: Decimal | None = None
    macd_hist: Decimal | None = None
    atr14: Decimal | None = None
    atr14_pct: Decimal | None = None
    volume_ma20: Decimal | None = None
    support_level: Decimal | None = None
    resistance_level: Decimal | None = None


class SignalListItem(_Base):
    """Lightweight payload for table views.

    Excludes the multi-KB free-text fields (`reason`, `risk_note`,
    `invalid_condition`, `follow_up_rule`) which would otherwise pad each row
    to 10-20 KB. Detail page (/api/signals/{id}) returns the full SignalOut.
    """

    id: int
    symbol: str
    market: str
    direction: str
    signal_type: str
    current_price: Decimal
    entry_low: Decimal | None = None
    entry_high: Decimal | None = None
    stop_loss: Decimal | None = None
    target_1: Decimal | None = None
    target_2: Decimal | None = None
    confidence_score: int
    risk_reward_ratio: Decimal | None = None
    position_size_pct: Decimal | None = None
    expected_holding_days_min: int | None = None
    expected_holding_days_max: int | None = None
    model_name: str
    status: str
    reject_reason: str | None = None
    valid_until: datetime
    created_at: datetime
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_cost_usd: Decimal | None = None


class SignalOut(_Base):
    id: int
    symbol: str
    market: str
    direction: str
    signal_type: str
    schema_version: str
    current_price: Decimal
    entry_low: Decimal | None = None
    entry_high: Decimal | None = None
    stop_loss: Decimal | None = None
    target_1: Decimal | None = None
    target_2: Decimal | None = None
    confidence_score: int
    risk_reward_ratio: Decimal | None = None
    position_size_pct: Decimal | None = None
    expected_holding_days_min: int | None = None
    expected_holding_days_max: int | None = None
    signal_decay_hours: int | None = None
    model_name: str
    reason: str
    risk_note: str
    invalid_condition: str
    follow_up_rule: str | None = None
    strategy_score: dict | None = None

    input_hash: str
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_input_tokens: int | None = None
    llm_output_tokens: int | None = None
    llm_cost_usd: Decimal | None = None
    prompt_version: str | None = None
    llm_call_log_id: int | None = None

    status: str
    reject_reason: str | None = None
    valid_until: datetime
    generation_batch_id: str
    created_at: datetime
    updated_at: datetime


class SignalSkipOut(_Base):
    id: int
    batch_id: str
    symbol: str
    reason: str
    detail: str | None = None
    score: int | None = None
    model_name: str | None = None
    created_at: datetime


class TradeListItem(_Base):
    """Light payload for tables; drops cost / fee / fill_policy / notes."""

    id: int
    signal_id: int
    symbol: str
    market: str
    direction: str
    model_name: str
    entry_time: datetime
    entry_price: Decimal
    quantity: Decimal
    position_value: Decimal
    stop_loss_initial: Decimal
    stop_loss_current: Decimal
    target_1: Decimal | None = None
    target_2: Decimal | None = None
    trailing_stop_activated: bool
    exit_time: datetime | None = None
    exit_price: Decimal | None = None
    exit_reason: str | None = None
    pnl_amount: Decimal | None = None
    pnl_pct: Decimal | None = None
    realized_r_multiple: Decimal | None = None
    status: str


class TradeOut(_Base):
    id: int
    signal_id: int
    symbol: str
    market: str
    direction: str
    model_name: str
    entry_time: datetime
    entry_price: Decimal
    entry_fill_policy: str
    quantity: Decimal
    position_value: Decimal
    slippage_paid: Decimal
    fee_paid: Decimal
    stop_loss_initial: Decimal
    target_1: Decimal | None = None
    target_2: Decimal | None = None
    max_holding_days: int | None = None
    stop_loss_current: Decimal
    trailing_stop_activated: bool
    exit_time: datetime | None = None
    exit_price: Decimal | None = None
    exit_reason: str | None = None
    exit_fill_policy: str | None = None
    pnl_amount: Decimal | None = None
    pnl_pct: Decimal | None = None
    realized_r_multiple: Decimal | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class RMultipleScatterPoint(_Base):
    """Tiny shape for the R-multiple scatter chart on /models."""

    exit_time: datetime
    realized_r_multiple: Decimal | None = None
    pnl_pct: Decimal | None = None
    symbol: str
    exit_reason: str | None = None


class PositionOut(_Base):
    id: int
    trade_id: int
    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    stop_loss_current: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    max_favorable_excursion: Decimal
    max_adverse_excursion: Decimal
    holding_days: int
    status: str
    updated_at: datetime


class PortfolioSnapshotOut(_Base):
    timestamp: datetime
    cash: Decimal
    equity: Decimal
    market_value: Decimal
    us_stock_exposure: Decimal
    crypto_exposure: Decimal
    daily_pnl: Decimal
    total_return_pct: Decimal
    max_drawdown_pct: Decimal
    open_positions_count: int
    consecutive_losses: int


class ReviewOut(_Base):
    id: int
    trade_id: int
    summary: str
    entry_quality: int
    exit_quality: int
    risk_control_quality: int
    what_worked: list[str]
    what_failed: list[str]
    model_adjustment_suggestion: str
    should_keep_model_signal: bool
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_cost_usd: Decimal | None = None
    llm_call_log_id: int | None = None
    created_at: datetime


class StrategyModelOut(_Base):
    id: int
    name: str
    description: str
    weight: Decimal
    is_active: bool
    auto_adjust_weight: bool
    created_at: datetime
    updated_at: datetime


class ModelStatOut(_Base):
    id: int
    model_name: str
    window: str
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: Decimal | None = None
    avg_win_pct: Decimal | None = None
    avg_loss_pct: Decimal | None = None
    profit_factor: Decimal | None = None
    expectancy: Decimal | None = None
    avg_r_multiple: Decimal | None = None
    sample_quality: str
    last_computed_at: datetime


class SystemHealthListItem(_Base):
    """Light shape: omits the `stats` dict which can be many KB."""

    id: int
    job_name: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    error_message: str | None = None
    created_at: datetime


class SystemHealthOut(_Base):
    id: int
    job_name: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    error_message: str | None = None
    stats: dict
    created_at: datetime


class LlmCallLogListItem(_Base):
    """Light shape for the LLM logs page listing."""

    id: int
    purpose: str
    provider: str
    model: str
    prompt_version: str
    cached: bool
    status: str
    symbol: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: Decimal | None = None
    latency_ms: int | None = None
    error_message: str | None = None
    attempts: int | None = None
    created_at: datetime


class LlmCallLogOut(_Base):
    """Full payload, including system_prompt / user_input / raw_response_text /
    thinking. Returned by GET /api/system/llm-logs/{id} so the user can audit
    exactly what was sent to and returned from the model.
    """

    id: int
    purpose: str
    provider: str
    model: str
    prompt_version: str
    input_hash: str
    cached: bool
    symbol: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: Decimal | None = None
    latency_ms: int | None = None
    status: str
    error_message: str | None = None
    attempts: int | None = None
    attempt_history: list | None = None
    system_prompt: str | None = None
    user_input: dict | list | str | None = None
    raw_response_text: str | None = None
    thinking: str | None = None
    response_payload: dict | list | str | None = None
    created_at: datetime


class ModelSummaryRow(_Base):
    """One row per StrategyModel: model + LAST_30D stats + recent R-multiples.

    Used by the /models page so the frontend doesn't have to fan out 1+N+N
    requests (one for the model list, one for stats per model, one for
    recent trades per model).
    """

    name: str
    description: str
    weight: Decimal
    is_active: bool
    auto_adjust_weight: bool
    stat: ModelStatOut | None = None
    recent_r_multiples: list[RMultipleScatterPoint] = []
