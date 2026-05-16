"""Candle (OHLCV bar) - TimescaleDB hypertable in production.

Per spec § 7.6 / § 8.1:
- timestamp stored as UTC TIMESTAMPTZ
- adjustment field is mandatory ("RAW" | "SPLIT_ADJUSTED")
- is_final flag mandatory; only is_final=True bars enter strategy chain
- (symbol, timeframe, timestamp) is unique
"""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PRICE = Numeric(20, 8)


class Candle(Base):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    open: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    high: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    low: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    close: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    volume: Mapped[Decimal] = mapped_column(PRICE, nullable=False)

    source: Mapped[str] = mapped_column(String(32), nullable=False)
    adjustment: Mapped[str] = mapped_column(String(32), nullable=False)  # SPLIT_ADJUSTED | RAW
    is_final: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_candles_sym_tf_ts"),
        Index("ix_candles_sym_tf_ts", "symbol", "timeframe", "timestamp"),
        Index("ix_candles_sym_tf_final", "symbol", "timeframe", "is_final"),
    )
