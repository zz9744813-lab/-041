"""Job helpers - SystemHealth wrapper per spec § 21.1."""
from datetime import datetime
from functools import wraps

from loguru import logger

from app.database import SessionLocal
from app.models import SystemHealth
from app.utils.time_utils import utc_now


def with_health_record(job_name: str):
    """Decorator: writes a SystemHealth row tracking this job's run.

    The wrapped function may accept `now: datetime | None = None`. The decorator
    will populate it via utc_now() if missing.

    The function should return a dict of stats (or None).
    """

    def decorator(func):
        @wraps(func)
        def wrapper(now: datetime | None = None):
            now = now or utc_now()
            db = SessionLocal()
            record = SystemHealth(
                job_name=job_name,
                started_at=now,
                status="RUNNING",
                stats={},
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            record_id = record.id
            db.close()

            try:
                stats = func(now) or {}
                _finalize(record_id, "SUCCESS", stats=stats)
                return stats
            except Exception as e:
                logger.exception("{} failed", job_name)
                _finalize(record_id, "FAILED", error_message=repr(e))
                # Don't re-raise; scheduler must keep running
                return {"error": str(e)}

        return wrapper

    return decorator


def _finalize(
    record_id: int,
    status: str,
    stats: dict | None = None,
    error_message: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        record = db.get(SystemHealth, record_id)
        if record:
            record.status = status
            record.finished_at = utc_now()
            if stats is not None:
                record.stats = stats
            if error_message:
                record.error_message = error_message
            db.commit()
    finally:
        db.close()
