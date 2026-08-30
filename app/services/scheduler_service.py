import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.contest_service import ContestService
from app.services.sourcing.contest_sourcing import ContestQuestionSourcing

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def sync_recent_and_upcoming_contests():
    """Fetches upcoming and recent contests to keep calendar fresh."""
    logger.info("Executing scheduled task: sync upcoming and recent contests")
    try:
        slugs = await ContestQuestionSourcing.fetch_upcoming_contest_slugs()
        for slug in slugs:
            await ContestService.sync_contest_metadata(slug)

        past_slugs = await ContestQuestionSourcing.fetch_past_contest_slugs(page=1)
        for slug in past_slugs[:2]:
            await ContestService.sync_contest_metadata(slug)
    except Exception as e:
        logger.error(f"Error in scheduled contest sync: {e}")


def start_scheduler():
    """Registers cron and interval triggers for contest synchronization and predictions."""
    # Sync upcoming contests every 30 minutes
    scheduler.add_job(
        sync_recent_and_upcoming_contests,
        trigger=IntervalTrigger(minutes=30),
        id="sync_upcoming_contests",
        replace_existing=True,
    )

    # Weekly contest rating prediction (Sunday 04:00 UTC)
    scheduler.add_job(
        sync_recent_and_upcoming_contests,
        trigger=CronTrigger(day_of_week="sun", hour=4, minute=0),
        id="weekly_contest_prediction",
        replace_existing=True,
    )

    # Biweekly contest rating prediction (Saturday 16:00 UTC)
    scheduler.add_job(
        sync_recent_and_upcoming_contests,
        trigger=CronTrigger(day_of_week="sat", hour=16, minute=0),
        id="biweekly_contest_prediction",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Contest background scheduler started")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Contest background scheduler stopped")
