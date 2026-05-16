"""System heartbeat job per spec § 21.5."""
from datetime import datetime

from app.jobs._helpers import with_health_record
from app.utils.time_utils import utc_now


@with_health_record("heartbeat")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    return {"heartbeat": True, "ts": now.isoformat()}
