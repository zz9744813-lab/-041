"""APScheduler bootstrap per spec § 16.4.

Run with: python -m app.scheduler
This is a separate process from FastAPI.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.config import get_settings
from app.jobs.calculate_indicators_job import run as run_indicators
from app.jobs.classify_market_regime_job import run as run_regime
from app.jobs.daily_report_job import run as run_daily
from app.jobs.generate_signals_job import run as run_signals
from app.jobs.model_stat_update_job import run as run_model_stat
from app.jobs.sync_market_data_job import run as run_sync
from app.jobs.system_health_heartbeat_job import run as run_heartbeat
from app.jobs.trade_review_job import run as run_review
from app.jobs.update_positions_job import run as run_update_positions
from app.utils.logging_utils import configure_logging


def _hourly_chain():
    """Chain: sync -> indicators -> update_positions."""
    run_sync()
    run_indicators()
    run_update_positions()


def _eod_chain():
    """End-of-day chain (UTC 21:00 ~ ET 17:00 EOD): full pipeline."""
    run_sync()
    run_indicators()
    run_regime()
    run_signals()
    run_update_positions()
    run_model_stat()
    run_review()
    run_daily()


def main():
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("scheduler starting up")

    sched = BlockingScheduler(timezone="UTC")

    # Heartbeat every 5 minutes
    sched.add_job(run_heartbeat, IntervalTrigger(minutes=5), id="heartbeat", replace_existing=True)

    # Hourly chain
    sched.add_job(_hourly_chain, CronTrigger(minute=5), id="hourly_chain", replace_existing=True)

    # End-of-day pipeline at UTC 21:05 (≈ ET 17:05)
    sched.add_job(_eod_chain, CronTrigger(hour=21, minute=5), id="eod_chain", replace_existing=True)

    # Crypto signals every 4h (00/04/08/12/16/20 UTC)
    sched.add_job(
        run_signals,
        CronTrigger(hour="0,4,8,12,16,20", minute=10),
        id="crypto_signals",
        replace_existing=True,
    )

    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("scheduler shutting down")


if __name__ == "__main__":
    main()
