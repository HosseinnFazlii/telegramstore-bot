import os
import sys
import django

sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from store.models import TelegramBotToken
from bot.handlers import (
    start_handler,
    phone_handler,
    menu1_handler,
    menu2_handler,
    image_slider_callback,
    coin1_callback,
    coin2_callback,
    back_to_menu_callback,
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

    # Command and message handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^09\d{9}$'), phone_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📦.*'), menu1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^💰'), menu2_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), start_handler))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(coin1_callback, pattern="^coin1$"))
    app.add_handler(CallbackQueryHandler(coin2_callback, pattern="^coin2$"))
    app.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(image_slider_callback))

    # Catch-all debug
    app.add_handler(MessageHandler(filters.ALL, debug_handler))

    logging.info("✅ Telegram Bot is running. Press Ctrl+C to stop.")
    app.run_polling()

# ✅ Fallback for unknown messages
async def debug_handler(update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text if update.message else "<no text>"
    logging.info(f"📩 DEBUG: Received: '{msg}' from user {update.effective_user.id}")
    await update.message.reply_text("✅ Bot received your message.")

if __name__ == "__main__":
    run_bot()
