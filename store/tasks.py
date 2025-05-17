import requests
import logging
from celery import shared_task
from django.utils.timezone import now, localtime
from .models import ChannelMessage
from store.models import TelegramBotToken
import os
import shutil
import datetime
import tempfile
import subprocess
import requests
import logging
from celery import shared_task
from store.models import TelegramBotToken
from django.conf import settings

@shared_task
def send_scheduled_messages():
    token_obj = TelegramBotToken.objects.first()
    if not token_obj:
        logging.error("❌ No bot token found in TelegramBotToken table.")
        return

    TELEGRAM_BOT_TOKEN = token_obj.token
    TELEGRAM_CHAT_ID = "-1002081294344"  # ✅ Public channel username (not ID)

    current_time = localtime(now())
    print(f"⏰ Task running at: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    daily_msgs = ChannelMessage.objects.filter(
        schedule_type="daily",
        scheduled_time__hour=current_time.hour,
        scheduled_time__minute=current_time.minute
    )
    once_msgs = ChannelMessage.objects.filter(
        schedule_type="once",
        scheduled_datetime__lte=current_time,
        sent=False
    )

    print(f"🔎 Found {daily_msgs.count()} daily messages.")
    print(f"🔎 Found {once_msgs.count()} one-time messages.")

    all_msgs = list(daily_msgs) + list(once_msgs)

    for msg in all_msgs:
        try:
            print(f"📤 Sending message: {msg.title}")
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg.message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )

            if response.status_code == 200:
                print(f"✅ Sent message: {msg.title}")
                if msg.schedule_type == "once":
                    msg.sent = True
                    msg.save()
            else:
                print(f"❌ Telegram API error for '{msg.title}': {response.text}")

        except Exception as e:
            logging.exception(f"❌ Exception sending message '{msg.title}': {e}")



@shared_task
def backup_project_and_send():
    try:
        # Read from environment or Django settings
        db_name = os.environ['DB_NAME']
        db_user = os.environ['DB_USER']
        db_password = os.environ['DB_PASSWORD']
        db_host = os.environ.get('DB_HOST', 'db')  # 'db' is the common Docker service name
        db_port = os.environ.get('DB_PORT', '5432')

        telegram_token = TelegramBotToken.objects.first().token
        telegram_user_id = '185097996'  # Add this to .env
        if not telegram_user_id:
            logging.warning("⚠️ No BACKUP_TELEGRAM_USER_ID specified.")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['PGPASSWORD'] = db_password  # Needed for pg_dump authentication

            backup_path = os.path.join(tmpdir, 'db_backup.sql')

            result = subprocess.run([
                'pg_dump',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-f', backup_path,
                db_name
            ], check=True)

            # Send to Telegram
            with open(backup_path, 'rb') as f:
                response = requests.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendDocument",
                    data={'chat_id': telegram_user_id, 'caption': '📦 DB Backup'},
                    files={'document': f}
                )
                if response.status_code != 200:
                    logging.error(f"Telegram send error: {response.text}")

    except Exception as e:
        logging.error(f"❌ Exception in backup task: {e}")