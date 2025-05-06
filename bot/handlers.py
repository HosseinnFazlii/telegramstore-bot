# bot/handlers.py
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from store.models import TelegramUser, Product, PreparedMessage
from asgiref.sync import sync_to_async

@sync_to_async
def get_msg_sync(title):
    return PreparedMessage.objects.filter(title__iexact=title).first()

@sync_to_async
def get_or_create_user_sync(telegram_id):
    return TelegramUser.objects.get_or_create(telegram_id=telegram_id)

@sync_to_async
def update_user_phone_sync(telegram_id, phone):
    TelegramUser.objects.filter(telegram_id=telegram_id).update(phone_number=phone)

@sync_to_async
def get_all_products_sync():
    return list(Product.objects.prefetch_related('images').all())

async def start_handler(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    user, created = await get_or_create_user_sync(telegram_id=telegram_id)

    if created:
        msg = await get_msg_sync("firsttime")
        if msg:
            await update.message.reply_text(msg.message)
    else:
        await show_main_menu(update)

async def phone_handler(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    if not re.match(r'^09\d{9}$', phone):
        msg = await get_msg_sync("error1")
        if msg:
            await update.message.reply_text(msg.message)
        return

    telegram_id = update.effective_user.id
    await update_user_phone_sync(telegram_id=telegram_id, phone_number=phone)
    await show_main_menu(update)

async def show_main_menu(update: Update):
    btn1 = await get_msg_sync("menue1")
    btn2 = await get_msg_sync("menue2")
    btn3 = await get_msg_sync("menue3")

    keyboard = [[
        KeyboardButton(btn1.message if btn1 else "Menu 1"),
        KeyboardButton(btn2.message if btn2 else "Menu 2"),
        KeyboardButton(btn3.message if btn3 else "Menu 3")
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    menu_msg = await get_msg_sync("main_menu")
    await update.message.reply_text(menu_msg.message if menu_msg else "Choose from below:", reply_markup=reply_markup)

async def menu1_handler(update: Update, context: CallbackContext):
    products = await get_all_products_sync()

    for product in products:
        caption = f"{product.name}\n{product.description}\n💰 {product.price} تومان\n⚖️ {product.weight} گرم"
        
        product_images = []
        if hasattr(product, 'images'):
            product_images = await sync_to_async(list)(product.images.all())

        for i, img in enumerate(product_images):
            current_caption = caption if i == 0 else None
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img.image.url, caption=current_caption)

    back_msg = await get_msg_sync("back_to_menu1")
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton(back_msg.message if back_msg else "🔙 Back")]], resize_keyboard=True)
    await update.message.reply_text(back_msg.message if back_msg else "Back to menu:", reply_markup=reply_markup)
