"""Trade review job - generate Reviews for trades closed today."""
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
        # Find CLOSED trades that don't have a review yet
        stmt = (
            select(Trade)
            .where(Trade.status == "CLOSED", Trade.exit_time >= cutoff)
        )
        trades = list(db.scalars(stmt).all())
        reviewed = 0
        skipped = 0
        for t in trades:
            existing = db.scalars(select(Review).where(Review.trade_id == t.id)).first()
            if existing:
                skipped += 1
                continue
            try:
                review_service.generate_for_trade(db, t.id, now=now)
                db.commit()
                reviewed += 1
            except Exception as e:
                db.rollback()
                skipped += 1
        return {"reviewed": reviewed, "skipped": skipped, "checked": len(trades)}
    finally:
        db.close()
