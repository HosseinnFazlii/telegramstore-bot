import asyncio
import logging
from django.core.management.base import BaseCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters, CallbackQueryHandler
)
from telegram import Update
from store.models import TelegramBotToken # Assuming store.models is the correct path
from bot.handlers import (
    start_handler, phone_handler, menu1_handler, menu2_handler, 
    menu3_handler, stats_button_handler, coin1_callback, coin2_callback,
    back_to_menu_callback, image_slider_callback, coin_detail_handler
)
from asgiref.sync import sync_to_async

# Logging setup (can be configured via Django settings as well)
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

@sync_to_async
def get_bot_token():
    # Ensure Django is set up if this is called outside full Django manage.py context
    # However, for a management command, Django setup is typically done by manage.py
    token = TelegramBotToken.objects.first()
    if not token:
        logger.error("❌ No Telegram bot token found in the database.")
    return token

# Catch-all handler for debugging
async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text if update.message else "<no text>"
    user_id = update.effective_user.id if update.effective_user else 'N/A'
    logger.info(f"📩 DEBUG: Received: '{msg}' from user {user_id}")
    # Reply for debug can be spammy, ensure it's desired or conditional
    # await update.message.reply_text(f"DEBUG: Echo: {msg}")

async def start_telegram_bot_logic():
    logger.info("Attempting to start bot with manual lifecycle management...")
    token_obj = await get_bot_token()
    if not token_obj:
        return

    app = ApplicationBuilder().token(token_obj.token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^09\d{9}$'), phone_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📦.*'), menu1_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^💰.*'), menu2_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^🔙.*'), start_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📞.*'), menu3_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^📊.*'), stats_button_handler))
    
    # Add callback query handlers for inline keyboards
    app.add_handler(CallbackQueryHandler(coin1_callback, pattern="^coin1$"))
    app.add_handler(CallbackQueryHandler(coin2_callback, pattern="^coin2$"))
    app.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(image_slider_callback, pattern="^(next_|prev_).*"))
    
    # Add handler for coin detail (when user selects a coin from the list)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), coin_detail_handler))
    
    # Debug handler should be last to catch any unhandled messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), debug_handler))

    stop_event = asyncio.Event()

    try:
        logger.info("Initializing application...")
        await app.initialize()
        
        logger.info("Starting updater polling...")
        if app.updater:
            await app.updater.start_polling()
        else:
            logger.warning("No updater found on application object. Polling will not start.")

        logger.info("Starting application (processing updates)...")
        await app.start()
        
        logger.info("✅ Telegram Bot is running. Press Ctrl+C to stop.")
        await stop_event.wait() # Keep running until stop_event is set (e.g., by KeyboardInterrupt)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received (KeyboardInterrupt/SystemExit). Stopping bot...")
        # asyncio.run() should handle KeyboardInterrupt and allow finally to run
    except Exception as e:
        logger.error(f"An unexpected error occurred during bot operation: {e}", exc_info=True)
    finally:
        logger.info("Performing cleanup and shutting down bot components...")
        if app.running:
            logger.info("Stopping application...")
            await app.stop()
        if app.updater and app.updater.running:
            logger.info("Stopping updater...")
            await app.updater.stop()
        logger.info("Shutting down application...")
        await app.shutdown()
        logger.info("Bot has been shut down.")

class Command(BaseCommand):
    help = 'Runs the Telegram bot application with manual lifecycle control'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Telegram bot via management command...'))
        try:
            asyncio.run(start_telegram_bot_logic())
        except Exception as e:
            # Catching general exceptions here as asyncio.run might raise them from the task
            logger.error(f"Critical error during asyncio.run: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f'Failed to run bot: {e}'))
        finally:
            self.stdout.write(self.style.SUCCESS('Telegram bot management command finished.')) 