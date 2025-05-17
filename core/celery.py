import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# ✅ Combine all scheduled tasks in one dictionary
app.conf.beat_schedule = {
    "fetch-gold-prices-every-hour": {
        "task": "gold.tasks.fetch_and_save_gold_prices",
        "schedule": 60.0,  # Every 1 hour
    },
    "send-telegram-channel-messages-every-minute": {
        "task": "store.tasks.send_scheduled_messages",
        "schedule": crontab(minute='*'),  # Every minute
    },
    "send-telegram-channel-backup-every-hour": {
        "task": "store.tasks.backup_project_and_send",
        "schedule": 3600.0,  # Every hour
    },
    "fetch-usd-price-every-hour": {
        "task": "dollor.tasks.fetch_and_save_usd_price",  # Make sure this path matches your app and task name
        "schedule": 60.0,  # Every 1 hour
    },
}
