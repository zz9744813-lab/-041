"""AI Composite per spec § 12.4 model D - aggregates all strategies and applies weights.

In V1 with ENABLE_LLM_DECISION=false, this returns a SignalPlan derived purely from the
top-scoring strategy (after weight). LLM augmentation goes in Step 9.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import StrategyModel
from app.strategies.base import StrategyInput, StrategyScore


@dataclass
class CompositeResult:
    best_score: StrategyScore | None
    all_scores: list[StrategyScore]
    weights_applied: dict[str, float]


def combine(
    db: Session,
    input: StrategyInput,
    sub_scores: list[StrategyScore],
) -> CompositeResult:
    """Apply per-strategy weight and pick the top.

    Per spec § 12.4 / § 12.5:
      effective_score = strategy.final_score * model_weight
    """
    weights: dict[str, float] = {}
    weighted: list[StrategyScore] = []
    for sc in sub_scores:
        m = db.query(StrategyModel).filter_by(name=sc.model_name).first()
        w = float(m.weight) if m and m.is_active else 1.0 if not m else 0.0
        weights[sc.model_name] = w
        adjusted = StrategyScore(**{**sc.__dict__, "final_score": int(sc.final_score * w)})
        weighted.append(adjusted)

    weighted.sort(key=lambda s: s.final_score, reverse=True)
    best = weighted[0] if weighted else None
    return CompositeResult(best_score=best, all_scores=weighted, weights_applied=weights)
