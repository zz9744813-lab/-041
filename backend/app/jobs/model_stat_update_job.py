"""Model stat update job."""
from datetime import datetime

from app.database import SessionLocal
from app.services import model_weight_service
from app.utils.time_utils import utc_now

from app.jobs._helpers import with_health_record


@with_health_record("model_stat_update")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        return model_weight_service.update_all(db, now)
    finally:
        db.close()
