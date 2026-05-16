"""SignalPlan schema per spec § 11.2 - the structured contract LLM/rule engine must satisfy."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import Direction, Market, SignalType


class SignalPlan(BaseModel):
    """The single source of truth for a signal coming out of LLM or the rule engine."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0")
    symbol: str
    market: Market
    direction: Direction
    signal_type: SignalType
    timeframe_basis: list[str] = Field(default_factory=lambda: ["1d", "4h", "1h"])
    current_price: Decimal

    entry_low: Decimal | None = None
    entry_high: Decimal | None = None
    stop_loss: Decimal | None = None
    target_1: Decimal | None = None
    target_2: Decimal | None = None

    confidence_score: int = Field(ge=0, le=100)
    risk_reward_ratio: Decimal | None = None
    position_size_pct: Decimal | None = Field(default=None, ge=0, le=100)
    expected_holding_days_min: int | None = None
    expected_holding_days_max: int | None = None
    signal_decay_hours: int | None = None

    reason: str = Field(min_length=1, max_length=2000)
    risk_note: str = Field(default="", max_length=2000)
    invalid_condition: str = Field(min_length=1, max_length=2000)
    follow_up_rule: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_consistency(self) -> "SignalPlan":
        # NO_TRADE / INSUFFICIENT_DATA must be WATCH and may have all entry/sl/target null
        if self.signal_type in (SignalType.NO_TRADE, SignalType.INSUFFICIENT_DATA):
            if self.direction != Direction.WATCH:
                raise ValueError(
                    f"{self.signal_type} requires direction=WATCH, got {self.direction}"
                )
            return self

        if self.direction == Direction.LONG:
            if self.entry_low is None or self.entry_high is None:
                raise ValueError("LONG requires entry_low and entry_high")
            if self.stop_loss is None:
                raise ValueError("LONG requires stop_loss")
            if self.target_1 is None:
                raise ValueError("LONG requires target_1")
            if self.entry_low > self.entry_high:
                raise ValueError("entry_low must be <= entry_high")
            if self.stop_loss >= self.entry_low:
                raise ValueError("LONG stop_loss must be < entry_low")
            if self.target_1 <= self.entry_high:
                raise ValueError("LONG target_1 must be > entry_high")
        return self


class SignalPlanInput(BaseModel):
    """The JSON we feed into the LLM. Hashed for caching."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    symbol: str
    market: Market
    current_price: Decimal
    market_regime: str
    daily: dict
    four_hour: dict
    one_hour: dict
    strategy_scores: dict
    portfolio_context: dict
    constraints: dict
    asof_timestamp: datetime
