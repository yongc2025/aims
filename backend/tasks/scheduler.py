"""AIMS scheduler entrypoint."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.agents.run_akshare_collector import collect_market_data
from backend.services.trade_calendar import is_trade_day, previous_trade_date

TIMEZONE = ZoneInfo("Asia/Shanghai")
logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _today() -> str:
    return datetime.now(TIMEZONE).date().isoformat()


def _sync_today(label: str) -> None:
    trade_date = _today()
    if not is_trade_day(trade_date):
        logger.info("Skip %s sync because %s is not a trade day", label, trade_date)
        return

    logger.info("Start %s full snapshot sync for %s", label, trade_date)
    collect_market_data(trade_date, preserve_realtime_snapshot=False)
    logger.info("Finished %s full snapshot sync for %s", label, trade_date)


def _sync_previous_trade_day() -> None:
    trade_date = previous_trade_date(_today())
    logger.info("Start 08:30 supplemental sync for %s", trade_date)
    collect_market_data(trade_date, preserve_realtime_snapshot=True)
    logger.info("Finished 08:30 supplemental sync for %s", trade_date)


def start_scheduler() -> BackgroundScheduler:
    """Start background scheduler for market snapshots."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    for hour, minute, label in (
        (15, 30, "15:30"),
        (18, 0, "18:00"),
        (21, 0, "21:00"),
    ):
        scheduler.add_job(
            _sync_today,
            CronTrigger(hour=hour, minute=minute, timezone=TIMEZONE),
            args=[label],
            id=f"market_snapshot_{hour:02d}{minute:02d}",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    scheduler.add_job(
        _sync_previous_trade_day,
        CronTrigger(hour=8, minute=30, timezone=TIMEZONE),
        id="market_snapshot_0830_previous_trade_day",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("AIMS scheduler started")
    return scheduler


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_scheduler()
