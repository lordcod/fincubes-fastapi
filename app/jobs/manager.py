from datetime import datetime, timedelta
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.core.config import settings
from app.jobs.jobs import daily_task, delete_unverified_user

_log = logging.getLogger(__name__)

jobstores = {
    "default": SQLAlchemyJobStore(url=settings.DATABASE_URL_JOBS)
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Europe/Moscow")


def start_scheduler():
    """Start scheduler and add static jobs."""
    scheduler.add_job(
        daily_task,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_task",
        replace_existing=True,
    )
    scheduler.start()
    _log.info("Scheduler started")


def shutdown_scheduler():
    scheduler.shutdown()
    _log.info("Scheduler stopped")


def schedule_user_deletion(user_id: int, hours_delay: int | float = 24):
    """Schedule deletion of unverified user."""
    run_date = datetime.now() + timedelta(hours=hours_delay)
    scheduler.add_job(
        delete_unverified_user,
        trigger="date",
        run_date=run_date,
        args=[user_id],
        id=f"delete_user_{user_id}",
        replace_existing=True,
    )
    _log.debug("Scheduled deletion of user %s in %s hours",
               user_id, hours_delay)
