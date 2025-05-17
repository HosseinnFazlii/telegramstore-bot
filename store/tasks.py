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
