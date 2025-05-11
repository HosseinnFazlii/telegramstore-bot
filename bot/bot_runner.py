import os
import sys
import django

sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from store.models import TelegramBotToken
from bot.handlers import (
    start_handler,
    phone_handler,
    menu1_handler,
    menu2_handler,
    image_slider_callback,
      # ✅ CORRECT IMPORT
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
    app.add_handler(MessageHandler(filters.Regex(r'^💰'), menu2_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), start_handler))
    app.add_handler(CallbackQueryHandler(callback_router))  # ✅ Unified router
    app.add_handler(MessageHandler(filters.ALL, debug_handler))

    logging.info("✅ Telegram Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


async def callback_router(update, context):
    data = update.callback_query.data
    if data in ("coin1", "coin2", "back_to_menu"):
        await menu2_handler(update, context)
    else:
        await image_slider_callback(update, context)


async def debug_handler(update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text if update.message else "<no text>"
    logging.info(f"📩 DEBUG: Received: '{msg}' from user {update.effective_user.id}")
    await update.message.reply_text("✅ Bot received your message.")


if __name__ == "__main__":
    run_bot()
