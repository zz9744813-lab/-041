"""Sync market data job.

Per spec § 16.3:
- Pulls candles for all active assets across 1d/4h/1h
- Skips US assets on non-trading days (writes SUCCESS with skipped reason)
- Wraps execution in SystemHealth record
"""
from datetime import datetime

from loguru import logger
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Asset
from app.models.enums import Market
from app.services import data_service
from app.utils.time_utils import is_us_trading_day, utc_now

from app.jobs._helpers import with_health_record


@with_health_record("sync_market_data")
def run(now: datetime | None = None) -> dict:
    now = now or utc_now()
    db = SessionLocal()
    try:
        assets = db.scalars(select(Asset).where(Asset.is_active.is_(True))).all()
        us_open = is_us_trading_day(now)
        all_stats: list[dict] = []
        for asset in assets:
            if asset.market == Market.US_STOCK.value and not us_open:
                all_stats.append({"symbol": asset.symbol, "skipped": "non_trading_day"})
                continue
            try:
                stats = data_service.sync_symbol(db, asset, now=now)
                all_stats.append(stats)
            except Exception as e:
                logger.exception("sync failed for {}", asset.symbol)
                all_stats.append({"symbol": asset.symbol, "error": str(e)})
        return {"us_trading_day": us_open, "results": all_stats}
    finally:
        db.close()
