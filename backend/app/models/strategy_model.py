"""StrategyModel + ModelStat per spec § 10.10 / § 10.11."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StrategyModel(Base):
    __tablename__ = "strategy_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("1.0"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_adjust_weight: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ModelStat(Base):
    __tablename__ = "model_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    window: Mapped[str] = mapped_column(String(16), nullable=False)  # ALL_TIME / LAST_30D / LAST_90D
    trade_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loss_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    avg_win_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    avg_loss_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    profit_factor: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    expectancy: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    avg_r_multiple: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    sharpe_simplified: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    sample_quality: Mapped[str] = mapped_column(String(16), default="INSUFFICIENT", nullable=False)
    last_computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (UniqueConstraint("model_name", "window", name="uq_modelstat_name_window"),)
