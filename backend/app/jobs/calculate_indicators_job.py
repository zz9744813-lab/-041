"""Calculate indicators job - runs after sync_market_data_job."""
from datetime import datetime

from loguru import logger
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Asset
from app.services import indicator_service
from app.utils.time_utils import utc_now

from app.jobs._helpers import with_health_record


@with_health_record("calculate_indicators")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        assets = db.scalars(select(Asset).where(Asset.is_active.is_(True))).all()
        all_stats = []
        for asset in assets:
            for tf in ("1d", "4h", "1h"):
                try:
                    s = indicator_service.compute_for_symbol(db, asset.symbol, tf, now=now)
                    s["symbol"] = asset.symbol
                    s["timeframe"] = tf
                    all_stats.append(s)
                except Exception as e:
                    logger.exception("indicator calc failed for {}/{}", asset.symbol, tf)
                    all_stats.append({"symbol": asset.symbol, "timeframe": tf, "error": str(e)})
        return {"results": all_stats}
    finally:
        db.close()
