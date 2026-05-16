"""Centralized enums per spec Appendix B."""
from enum import Enum


class Direction(str, Enum):
    LONG = "LONG"
    WATCH = "WATCH"
    EXIT = "EXIT"


class SignalType(str, Enum):
    TREND_BREAKOUT = "TREND_BREAKOUT"
    PULLBACK_BUY = "PULLBACK_BUY"
    TREND_FOLLOW = "TREND_FOLLOW"
    RISK_WARNING = "RISK_WARNING"
    NO_TRADE = "NO_TRADE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SignalStatus(str, Enum):
    NEW = "NEW"
    APPROVED = "APPROVED"
    APPROVED_WAITING_ENTRY = "APPROVED_WAITING_ENTRY"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ExitReason(str, Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT_1 = "TAKE_PROFIT_1"
    TAKE_PROFIT_2 = "TAKE_PROFIT_2"
    TRAILING_STOP = "TRAILING_STOP"
    AI_RISK_EXIT = "AI_RISK_EXIT"
    MAX_HOLDING = "MAX_HOLDING"
    MANUAL = "MANUAL"


class MarketRegimeEnum(str, Enum):
    STRONG_BULL = "STRONG_BULL"
    MILD_BULL = "MILD_BULL"
    RANGE = "RANGE"
    MILD_BEAR = "MILD_BEAR"
    STRONG_BEAR = "STRONG_BEAR"
    HIGH_VOL_PANIC = "HIGH_VOL_PANIC"


class SampleQuality(str, Enum):
    INSUFFICIENT = "INSUFFICIENT"
    LOW = "LOW"
    ADEQUATE = "ADEQUATE"
    GOOD = "GOOD"


class JobStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Market(str, Enum):
    US_STOCK = "US_STOCK"
    CRYPTO = "CRYPTO"


class AssetType(str, Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    CRYPTO = "CRYPTO"


class Adjustment(str, Enum):
    RAW = "RAW"
    SPLIT_ADJUSTED = "SPLIT_ADJUSTED"


class Timeframe(str, Enum):
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class StatWindow(str, Enum):
    ALL_TIME = "ALL_TIME"
    LAST_30D = "LAST_30D"
    LAST_90D = "LAST_90D"
