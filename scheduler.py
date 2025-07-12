from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz
from main import scheduled_parsing

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))

def start_schedule():
    scheduler.add_job(scheduled_parsing, 'cron', hour=8, minute=0)
    scheduler.start()