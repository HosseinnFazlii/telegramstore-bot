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
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from telegram import Update
from store.models import TelegramBotToken
from asgiref.sync import sync_to_async

# ✅ Import handlers here
from bot.handlers import start_handler, phone_handler, menu1_handler

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

@sync_to_async
def get_bot_token():
    return TelegramBotToken.objects.first()

# 🔍 Catch-all fallback for testing
async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text if update.message else "<no text>"
    logging.info(f"📩 Received unknown message: {msg}")
    await update.message.reply_text("✅ Bot is alive. You said: " + msg)

# 🔍 TEMP: Debug version of start_handler to test /start
async def test_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("🚀 /start command received")
    await update.message.reply_text("👋 Hello! Bot received /start successfully.")

async def start_bot():
    token_obj = await get_bot_token()
    if not token_obj:
        print("❌ No Telegram bot token found.")
        return

    app = ApplicationBuilder().token(token_obj.token).build()

    # ✅ Register handlers
    app.add_handler(CommandHandler("start", test_start_handler))  # 👈 TEMP: confirm /start
    app.add_handler(MessageHandler(filters.Regex(r'^09\d{9}$'), phone_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📦.*'), menu1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), test_start_handler))
    app.add_handler(MessageHandler(filters.ALL, debug_handler))

    print("✅ Bot is running and polling...")
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.run(start_bot())
