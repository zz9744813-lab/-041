"""MarketRegime - daily classification per spec § 13."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketRegime(Base):
    __tablename__ = "market_regimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), unique=True, nullable=False, index=True
    )
    regime: Mapped[str] = mapped_column(String(32), nullable=False)
    spy_above_ma200: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spy_above_ma50: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vix_level: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    btc_above_ma200: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
