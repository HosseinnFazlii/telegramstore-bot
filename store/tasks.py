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
import requests
import logging
from celery import shared_task
from store.models import TelegramBotToken


@shared_task
def backup_project_and_send():
    try:
        # Step 1: Prepare backup ZIP
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        temp_dir = tempfile.mkdtemp()
        backup_filename = f"project_backup_{now}.zip"
        backup_path = os.path.join(temp_dir, backup_filename)

        shutil.make_archive(backup_path.replace(".zip", ""), 'zip', root_dir="/app")

        # Step 2: Get bot token and chat ID
        token_obj = TelegramBotToken.objects.first()
        if not token_obj:
            print("❌ No Telegram bot token found.")
            return

        TELEGRAM_BOT_TOKEN = token_obj.token
        TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_ID"  # 🛑 Replace with your numeric Telegram ID (e.g., 123456789)

        # Step 3: Send file via Telegram HTTP API
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

        with open(backup_path, 'rb') as doc_file:
            files = {"document": (backup_filename, doc_file)}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": f"🗂 Daily Project Backup - {now}",
            }
            response = requests.post(telegram_url, data=data, files=files, timeout=30)

        if response.status_code == 200:
            print("✅ Backup sent successfully.")
        else:
            logging.error(f"❌ Failed to send backup: {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Exception in backup task: {e}")