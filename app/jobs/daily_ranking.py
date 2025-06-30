import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from app.repositories.ratings import update_ratings
from app.shared.clients.redis import client

scheduler = BackgroundScheduler()


def daily_task():
    asyncio.create_task(update_ratings(client))


def start_scheduler():
    scheduler.add_job(daily_task, "cron", hour=0, minute=0, id="daily_task")
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
