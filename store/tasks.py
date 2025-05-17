import requests
import logging
from celery import shared_task
from django.utils.timezone import now, localtime
from .models import ChannelMessage
from store.models import TelegramBotToken

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
def backup_project_and_send():
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        temp_dir = tempfile.mkdtemp()
        backup_root = os.path.join(temp_dir, "project_backup")
        os.makedirs(backup_root)

        # Step 1: Dump PostgreSQL database
        db_filename = os.path.join(backup_root, "db_backup.sql")
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']
        db_host = settings.DATABASES['default'].get('HOST', 'localhost')
        db_port = settings.DATABASES['default'].get('PORT', '5432')

        env = os.environ.copy()
        env['PGPASSWORD'] = db_password

        dump_cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-f', db_filename,
            db_name
        ]
        subprocess.run(dump_cmd, env=env, check=True)

        # Step 2: Copy project files
        shutil.copytree("/app", os.path.join(backup_root, "project"))

        # Step 3: Zip everything
        zip_path = os.path.join(temp_dir, f"project_backup_{now}.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', root_dir=backup_root)

        # Step 4: Send ZIP to Telegram
        token_obj = TelegramBotToken.objects.first()
        if not token_obj:
            print("❌ No Telegram bot token found.")
            return

        TELEGRAM_BOT_TOKEN = token_obj.token
        TELEGRAM_CHAT_ID = "185097996"  # Replace with your actual ID

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

        with open(zip_path, 'rb') as doc_file:
            files = {"document": (f"backup_{now}.zip", doc_file)}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": f"📦 Full backup including DB — {now}"
            }
            response = requests.post(telegram_url, data=data, files=files, timeout=30)

        if response.status_code == 200:
            print("✅ Backup sent successfully.")
        else:
            logging.error(f"❌ Failed to send backup: {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Exception in backup task: {e}")