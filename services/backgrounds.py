import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from misc.ratings import update_ratings

scheduler = BackgroundScheduler()


def daily_task():
    asyncio.create_task(update_ratings())


def start_scheduler():
    scheduler.add_job(daily_task, 'cron', hour=0, minute=0, id='daily_task')
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
