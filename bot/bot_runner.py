import os
import sys
import django

# Load Django settings
sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from store.models import TelegramBotToken
from asgiref.sync import sync_to_async

from bot.handlers import (
    start_handler, phone_handler, menu1_handler, image_slider_callback
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

@sync_to_async
def get_bot_token():
    return TelegramBotToken.objects.first()

async def debug_handler(update, context):
    msg = update.message.text if update.message else "<no text>"
    logging.info(f"📩 DEBUG: Received: '{msg}' from user {update.effective_user.id}")
    await update.message.reply_text("✅ Bot received your message.")

async def run_bot():
    token_obj = await get_bot_token()
    if not token_obj:
        print("❌ No Telegram bot token found in the database.")
        return

    app = ApplicationBuilder().token(token_obj.token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^09\d{9}$'), phone_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📦.*'), menu1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), start_handler))
    app.add_handler(MessageHandler(filters.ALL, debug_handler))
    app.add_handler(CallbackQueryHandler(image_slider_callback))

    logging.info("✅ Telegram Bot is running. Press Ctrl+C to stop.")
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.run(run_bot())
