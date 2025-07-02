from apscheduler.schedulers.background import BackgroundScheduler

from app.repositories.ratings import update_ratings
from app.shared.clients.redis import client

scheduler = BackgroundScheduler()


async def daily_task():
    await update_ratings(client)


def start_scheduler():
    scheduler.add_job(daily_task, "cron", hour=16, minute=50, id="daily_task")
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
