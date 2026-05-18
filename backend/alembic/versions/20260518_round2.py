"""Round-2 schema additions: indexes, signal.strategy_score JSON, signal_skips
table, llm_call_logs.attempt_history + symbol.

Revision ID: 20260518_round2
Revises: 20260518_llm_visibility
Create Date: 2026-05-18

This migration is additive and safe to apply on top of round-1; everything is
nullable / has defaults / is index-only.
"""
from alembic import op
import sqlalchemy as sa


revision = "20260518_round2"
down_revision = "20260518_llm_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- New SignalSkip table ----
    op.create_table(
        "signal_skips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.String(36), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_signal_skips_batch_id", "signal_skips", ["batch_id"])
    op.create_index("ix_signal_skips_symbol", "signal_skips", ["symbol"])
    op.create_index("ix_signal_skips_created_at", "signal_skips", ["created_at"])
    op.create_index(
        "ix_signal_skips_symbol_created", "signal_skips", ["symbol", "created_at"]
    )

    # ---- Signal.strategy_score ----
    op.add_column("signals", sa.Column("strategy_score", sa.JSON(), nullable=True))

    # ---- Trade composite indexes ----
    op.create_index(
        "ix_trades_status_exit_time", "trades", ["status", "exit_time"], unique=False
    )
    op.create_index("ix_trades_signal_id", "trades", ["signal_id"], unique=False)

    # ---- Position.status index ----
    op.create_index("ix_positions_status", "positions", ["status"], unique=False)

    # ---- Review.created_at index ----
    op.create_index("ix_reviews_created_at", "reviews", ["created_at"], unique=False)

    # ---- LlmCallLog.attempt_history + symbol ----
    op.add_column("llm_call_logs", sa.Column("attempt_history", sa.JSON(), nullable=True))
    op.add_column("llm_call_logs", sa.Column("symbol", sa.String(32), nullable=True))
    op.create_index("ix_llm_call_logs_symbol", "llm_call_logs", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_llm_call_logs_symbol", table_name="llm_call_logs")
    op.drop_column("llm_call_logs", "symbol")
    op.drop_column("llm_call_logs", "attempt_history")

    op.drop_index("ix_reviews_created_at", table_name="reviews")
    op.drop_index("ix_positions_status", table_name="positions")
    op.drop_index("ix_trades_signal_id", table_name="trades")
    op.drop_index("ix_trades_status_exit_time", table_name="trades")

    op.drop_column("signals", "strategy_score")

    op.drop_index("ix_signal_skips_symbol_created", table_name="signal_skips")
    op.drop_index("ix_signal_skips_created_at", table_name="signal_skips")
    op.drop_index("ix_signal_skips_symbol", table_name="signal_skips")
    op.drop_index("ix_signal_skips_batch_id", table_name="signal_skips")
    op.drop_table("signal_skips")
