"""LLM visibility v2: add audit columns to llm_call_logs + FK on signals/reviews.

Revision ID: 20260518_llm_visibility
Revises:
Create Date: 2026-05-18

This migration adds:
  - llm_call_logs.system_prompt           Text
  - llm_call_logs.user_input              JSON
  - llm_call_logs.raw_response_text       Text
  - llm_call_logs.thinking                Text
  - llm_call_logs.attempts                Integer
  - signals.llm_call_log_id               FK -> llm_call_logs.id
  - reviews.llm_call_log_id               FK -> llm_call_logs.id

These are all nullable + indexed-where-relevant so the migration is safe to
apply on top of an existing DB without backfilling.
"""
from alembic import op
import sqlalchemy as sa


revision = "20260518_llm_visibility"
# Adjust this if you have an earlier revision; alembic will warn otherwise.
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # llm_call_logs new audit columns
    op.add_column("llm_call_logs", sa.Column("system_prompt", sa.Text(), nullable=True))
    op.add_column("llm_call_logs", sa.Column("user_input", sa.JSON(), nullable=True))
    op.add_column("llm_call_logs", sa.Column("raw_response_text", sa.Text(), nullable=True))
    op.add_column("llm_call_logs", sa.Column("thinking", sa.Text(), nullable=True))
    op.add_column("llm_call_logs", sa.Column("attempts", sa.Integer(), nullable=True))

    # signals -> llm_call_logs FK
    op.add_column(
        "signals",
        sa.Column("llm_call_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_signals_llm_call_log_id", "signals", ["llm_call_log_id"], unique=False
    )
    op.create_foreign_key(
        "fk_signals_llm_call_log_id",
        "signals",
        "llm_call_logs",
        ["llm_call_log_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # reviews -> llm_call_logs FK
    op.add_column(
        "reviews",
        sa.Column("llm_call_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_reviews_llm_call_log_id", "reviews", ["llm_call_log_id"], unique=False
    )
    op.create_foreign_key(
        "fk_reviews_llm_call_log_id",
        "reviews",
        "llm_call_logs",
        ["llm_call_log_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_reviews_llm_call_log_id", "reviews", type_="foreignkey")
    op.drop_index("ix_reviews_llm_call_log_id", table_name="reviews")
    op.drop_column("reviews", "llm_call_log_id")

    op.drop_constraint("fk_signals_llm_call_log_id", "signals", type_="foreignkey")
    op.drop_index("ix_signals_llm_call_log_id", table_name="signals")
    op.drop_column("signals", "llm_call_log_id")

    op.drop_column("llm_call_logs", "attempts")
    op.drop_column("llm_call_logs", "thinking")
    op.drop_column("llm_call_logs", "raw_response_text")
    op.drop_column("llm_call_logs", "user_input")
    op.drop_column("llm_call_logs", "system_prompt")
