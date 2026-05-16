"""Signal + SignalLifecycle per spec § 10.5."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PRICE = Numeric(20, 8)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(16), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)

    current_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    entry_low: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    entry_high: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    target_1: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    target_2: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)

    confidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_reward_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    position_size_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    expected_holding_days_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_holding_days_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signal_decay_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    risk_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    invalid_condition: Mapped[str] = mapped_column(Text, default="", nullable=False)
    follow_up_rule: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---- LLM tracking (V2 § 8.5) ----
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    llm_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # ---- Lifecycle (V2 § 8.4) ----
    status: Mapped[str] = mapped_column(String(32), default="NEW", nullable=False)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generation_batch_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

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
        Index("ix_signals_sym_status", "symbol", "status"),
        Index("ix_signals_created_at", "created_at"),
    )
