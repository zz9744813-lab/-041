"""RiskDecision schema per spec § 14.3."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RiskDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    adjusted_position_size_pct: Decimal | None = None
    reject_reason: str | None = None
    warnings: list[str] = []
    triggered_rules: list[str] = []
