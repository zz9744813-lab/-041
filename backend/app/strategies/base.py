"""Strategy scoring base classes per spec section 12.

A strategy reads StrategyInput and returns StrategyScore. Pure rules - no LLM.
Strategy scores feed the AI Composite (which optionally calls LLM).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.models import Asset, Candle, IndicatorSnapshot, MarketRegime, PortfolioSnapshot, Position, Signal


@dataclass
class StrategyInput:
    asset: Asset
    latest_candles_1d: list[Candle]
    latest_candles_4h: list[Candle]
    latest_candles_1h: list[Candle]
    indicators_1d: IndicatorSnapshot | None
    indicators_4h: IndicatorSnapshot | None
    indicators_1h: IndicatorSnapshot | None
    market_regime: MarketRegime | None
    open_positions: list[Position] = field(default_factory=list)
    recent_signals: list[Signal] = field(default_factory=list)
    portfolio_snapshot: PortfolioSnapshot | None = None
    now: datetime | None = None


@dataclass
class StrategyScore:
    symbol: str
    model_name: str
    trend_score: int = 0
    setup_score: int = 0
    risk_score: int = 0
    volume_score: int = 0
    market_regime_score: int = 0
    risk_reward_score: int = 0
    final_score: int = 0
    suggested_action: str = "WATCH"  # ENTER | WATCH | AVOID
    raw_reason: str = ""

    # Optional candidate prices for the rule-based signal generator
    entry_low: Decimal | None = None
    entry_high: Decimal | None = None
    stop_loss: Decimal | None = None
    target_1: Decimal | None = None
    target_2: Decimal | None = None


class BaseStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def score(self, input: StrategyInput) -> StrategyScore:
        ...

    def _empty_score(self, asset: Asset, reason: str) -> StrategyScore:
        return StrategyScore(
            symbol=asset.symbol,
            model_name=self.name,
            suggested_action="WATCH",
            raw_reason=reason,
        )
