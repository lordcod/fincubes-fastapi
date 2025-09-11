from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.repositories.ratings import update_ratings
from app.shared.clients.mongodb import db

scheduler = AsyncIOScheduler()


async def daily_task():
    await update_ratings(db['ranking'])


def start_scheduler():
    scheduler.add_job(daily_task, "cron", hour=0, minute=0, id="daily_task")
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
