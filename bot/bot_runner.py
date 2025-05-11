import os
import sys
import django

sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from store.models import TelegramBotToken
from bot.handlers import (
    start_handler, phone_handler, menu1_handler, image_slider_callback,
    menu2_handler, coin1_handler, coin2_handler
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def run_bot():
    token_obj = TelegramBotToken.objects.first()
    if not token_obj:
        print("❌ No Telegram bot token found in the database.")
        return

    app = ApplicationBuilder().token(token_obj.token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^09\d{9}$'), phone_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📦.*'), menu1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^💰.*'), menu2_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🪙.*'), coin1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🏺.*'), coin2_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), start_handler))
    app.add_handler(MessageHandler(filters.ALL, debug_handler))
    app.add_handler(CallbackQueryHandler(image_slider_callback))

    logging.info("✅ Telegram Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


def debug_handler(update, context):
    msg = update.message.text if update.message else "<no text>"
    logging.info(f"📩 DEBUG: Received: '{msg}' from user {update.effective_user.id}")
    update.message.reply_text("✅ Bot received your message.")


if __name__ == "__main__":
    run_bot()
