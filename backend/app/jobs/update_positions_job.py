"""Update positions job."""
from datetime import datetime

from app.database import SessionLocal
from app.services import paper_trading_service
from app.utils.time_utils import utc_now

from app.jobs._helpers import with_health_record


@with_health_record("update_positions")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        return paper_trading_service.update_all_open_positions(db, now)
    finally:
        db.close()
