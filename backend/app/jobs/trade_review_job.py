"""Trade review job - generate Reviews for trades closed today.

v2.1: bulk-loads existing review trade_ids in one query instead of N+1.
"""
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.jobs._helpers import with_health_record
from app.models import Review, Trade
from app.services import review_service
from app.utils.time_utils import utc_now


@with_health_record("trade_review")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        cutoff = now - timedelta(days=1)
        trades = list(
            db.scalars(
                select(Trade).where(Trade.status == "CLOSED", Trade.exit_time >= cutoff)
            ).all()
        )
        if not trades:
            return {"reviewed": 0, "skipped": 0, "checked": 0}

        trade_ids = [t.id for t in trades]
        existing_ids: set[int] = set(
            db.scalars(select(Review.trade_id).where(Review.trade_id.in_(trade_ids))).all()
        )

        reviewed = 0
        skipped = 0
        for t in trades:
            if t.id in existing_ids:
                skipped += 1
                continue
            try:
                review_service.generate_for_trade(db, t.id, now=now)
                db.commit()
                reviewed += 1
            except Exception:
                db.rollback()
                skipped += 1
        return {"reviewed": reviewed, "skipped": skipped, "checked": len(trades)}
    finally:
        db.close()
