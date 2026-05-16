"""Classify market regime job."""
from datetime import datetime

from app.database import SessionLocal
from app.services import market_regime_service
from app.utils.time_utils import utc_now

from app.jobs._helpers import with_health_record


@with_health_record("classify_market_regime")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        row = market_regime_service.classify(db, now=now)
        if row is None:
            return {"skipped": "insufficient_data"}
        return {"regime": row.regime, "notes": row.notes}
    finally:
        db.close()
