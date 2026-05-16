"""Review per spec § 10.9."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trades.id"), unique=True, nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    entry_quality: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    exit_quality: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    risk_control_quality: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    what_worked: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    what_failed: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    model_adjustment_suggestion: Mapped[str] = mapped_column(Text, default="", nullable=False)
    should_keep_model_signal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
