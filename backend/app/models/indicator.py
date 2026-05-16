"""IndicatorSnapshot - per (symbol, timeframe, timestamp).

Per spec § 8.2:
- Only emitted for is_final=True candles
- based_on_closed_bar flag is the strategy chain gate
"""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PRICE = Numeric(20, 8)


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    based_on_closed_bar: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    ma20: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    ma50: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    ma200: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    ema20: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    ema50: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)

    rsi14: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    macd: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    macd_signal: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    macd_hist: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)

    atr14: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    atr14_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    volume_ma20: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)

    support_level: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    resistance_level: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    bbands_upper: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    bbands_lower: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_indi_sym_tf_ts"),
        Index("ix_indi_sym_tf_ts", "symbol", "timeframe", "timestamp"),
    )
