import os
import sys
import django

# Ensure Django settings are loaded
sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from telegram import Update
from store.models import TelegramBotToken
from bot.handlers import start_handler, phone_handler, menu1_handler
from asgiref.sync import sync_to_async

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

@sync_to_async
def get_bot_token():
    return TelegramBotToken.objects.first()

# Catch-all handler for debugging
async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text if update.message else "<no text>"
    logging.info(f"📩 Received: {msg}")
    await update.message.reply_text("✅ Bot is alive. You said: " + msg)

async def start_bot():
    token_obj = await get_bot_token()
    if not token_obj:
        print("❌ No Telegram bot token found.")
        return

    app = ApplicationBuilder().token(token_obj.token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^09\d{9}$'), phone_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📦.*'), menu1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), start_handler))
    app.add_handler(MessageHandler(filters.ALL, debug_handler))

    print("✅ Bot is running...")
    # app.run_polling() handles initialization, starting, polling, and shutdown.
    await app.run_polling(close_loop=False)

# ✅ Entry point: use existing loop
if __name__ == "__main__":
    asyncio.run(start_bot())
