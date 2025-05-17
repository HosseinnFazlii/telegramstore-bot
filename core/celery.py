import os
from celery import Celery

from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # Update 'core' with your project name

app = Celery("core")  # Replace 'core' with your actual project name

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in Django apps
app.autodiscover_tasks()

# Define the Celery schedule for periodic tasks
app.conf.beat_schedule = {
    "fetch-gold-prices-every-hour": {
        "task": "gold.tasks.fetch_and_save_gold_prices",
        "schedule": 60.0,  # Every 1 hour (in seconds)
    },
}


app.conf.beat_schedule = {
    'send-telegram-channel-messages-every-minute': {
        'task': 'store.tasks.send_scheduled_messages',
        'schedule': crontab(minute='*'),  # every minute
    },
}

app.conf.beat_schedule = {
    'send-telegram-channel-messages-every-minute': {
         'task': 'store.tasks.backup_project_and_send',
        "schedule": 120.0,  # every minute
    },
}