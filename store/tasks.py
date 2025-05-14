from celery import shared_task
from .models import ChannelMessage
from telegram import Bot
from store.models import TelegramBotToken
from django.utils.timezone import now

@shared_task
def send_scheduled_messages():
    token_obj = TelegramBotToken.objects.first()
    if not token_obj:
        print("❌ No bot token found in TelegramBotToken table.")
        return

    bot = Bot(token=token_obj.token)
    channel_id = "@your_channel_username"  # Replace with your actual channel ID

    current_time = now()

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

    for msg in daily_msgs | once_msgs:
        try:
            bot.send_message(chat_id=channel_id, text=msg.message)
            if msg.schedule_type == "once":
                msg.sent = True
                msg.save()
        except Exception as e:
            print(f"❌ Failed to send message '{msg.title}': {e}")