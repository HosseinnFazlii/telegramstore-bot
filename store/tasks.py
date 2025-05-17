from celery import shared_task
from .models import ChannelMessage
from telegram import Bot
from store.models import TelegramBotToken
from django.utils.timezone import now, localtime
import traceback

@shared_task
def send_scheduled_messages():
    token_obj = TelegramBotToken.objects.first()
    if not token_obj:
        print("❌ No bot token found in TelegramBotToken table.")
        return

    bot = Bot(token=token_obj.token)
    channel_id = "@tala_faramarzi"  # Replace with your actual channel ID

    current_time = localtime(now())  # use local (Tehran) time
    print(f"⏰ Task running at: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Daily messages: match time only (hours and minutes)
    daily_msgs = ChannelMessage.objects.filter(
        schedule_type="daily",
        scheduled_time__hour=current_time.hour,
        scheduled_time__minute=current_time.minute
    )

    # One-time messages: scheduled for this time and not sent yet
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
            bot.send_message(chat_id=channel_id, text=msg.message)
            print(f"✅ Sent message: {msg.title}")
            if msg.schedule_type == "once":
                msg.sent = True
                msg.save()
        except Exception as e:
            print(f"❌ Failed to send message '{msg.title}': {e}")
            traceback.print_exc()
