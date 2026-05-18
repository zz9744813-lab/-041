"""Trade + Position per spec § 10.6 / § 10.7."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PRICE = Numeric(20, 8)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), nullable=False)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(16), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # ---- Entry ----
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    entry_fill_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    position_value: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    slippage_paid: Mapped[Decimal] = mapped_column(PRICE, default=Decimal("0"), nullable=False)
    fee_paid: Mapped[Decimal] = mapped_column(PRICE, default=Decimal("0"), nullable=False)

    # ---- Risk parameters (snapshot at open, never modified) ----
    stop_loss_initial: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    target_1: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    target_2: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    max_holding_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ---- Trailing stop ----
    stop_loss_current: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    trailing_stop_activated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ---- Exit ----
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_price: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exit_fill_policy: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ---- P&L ----
    pnl_amount: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    pnl_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    realized_r_multiple: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
        Index("ix_trades_status", "status"),
        Index("ix_trades_symbol", "symbol"),
        Index("ix_trades_model", "model_name"),
        Index("ix_trades_entry_time", "entry_time"),
        # Used by /api/trades?status=CLOSED ordered by exit_time and by
        # daily_report_job's "today's closed pnl" query.
        Index("ix_trades_status_exit_time", "status", "exit_time"),
        # /api/signals/{id}/trade and /api/trades?signal_id=N
        Index("ix_trades_signal_id", "signal_id"),
    )


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trades.id"), nullable=False, unique=True
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    avg_entry_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    stop_loss_current: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(PRICE, default=Decimal("0"), nullable=False)
    unrealized_pnl_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0"), nullable=False
    )
    max_favorable_excursion: Mapped[Decimal] = mapped_column(
        PRICE, default=Decimal("0"), nullable=False
    )
    max_adverse_excursion: Mapped[Decimal] = mapped_column(
        PRICE, default=Decimal("0"), nullable=False
    )
    holding_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="OPEN", nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
