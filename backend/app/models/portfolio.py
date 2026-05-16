"""PortfolioSnapshot per spec § 10.8."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PRICE = Numeric(20, 8)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), unique=True, nullable=False, index=True
    )
    cash: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    equity: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    market_value: Mapped[Decimal] = mapped_column(PRICE, default=Decimal("0"), nullable=False)
    us_stock_exposure: Mapped[Decimal] = mapped_column(
        PRICE, default=Decimal("0"), nullable=False
    )
    crypto_exposure: Mapped[Decimal] = mapped_column(
        PRICE, default=Decimal("0"), nullable=False
    )
    daily_pnl: Mapped[Decimal] = mapped_column(PRICE, default=Decimal("0"), nullable=False)
    total_return_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0"), nullable=False
    )
    max_drawdown_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0"), nullable=False
    )
    open_positions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consecutive_losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
