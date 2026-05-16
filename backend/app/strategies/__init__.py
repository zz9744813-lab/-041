"""Strategies package."""
from app.strategies.ai_composite import CompositeResult, combine
from app.strategies.base import BaseStrategy, StrategyInput, StrategyScore
from app.strategies.moving_average_trend import MovingAverageTrendStrategy
from app.strategies.pullback_trend import PullbackTrendStrategy
from app.strategies.trend_breakout import TrendBreakoutStrategy

ALL_STRATEGIES: list[BaseStrategy] = [
    TrendBreakoutStrategy(),
    PullbackTrendStrategy(),
    MovingAverageTrendStrategy(),
]

__all__ = [
    "ALL_STRATEGIES",
    "BaseStrategy",
    "CompositeResult",
    "MovingAverageTrendStrategy",
    "PullbackTrendStrategy",
    "StrategyInput",
    "StrategyScore",
    "TrendBreakoutStrategy",
    "combine",
]
