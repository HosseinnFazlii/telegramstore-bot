import re
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton, InputMediaPhoto
)
from telegram.ext import CallbackContext
from store.models import TelegramUser, Product, PreparedMessage
from asgiref.sync import sync_to_async
from django.conf import settings


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

@sync_to_async
def user_has_phone_sync(telegram_id):
    user = TelegramUser.objects.filter(telegram_id=telegram_id, phone_number__isnull=False).first()
    return bool(user)

@sync_to_async
def get_product_by_id(product_id):
    return Product.objects.prefetch_related('images').get(id=product_id)


async def start_handler(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    user, created = await get_or_create_user_sync(telegram_id=telegram_id)
    if user.phone_number:
        await show_main_menu(update)
    else:
        msg = await get_msg_sync("firsttime")
        if msg:
            await update.message.reply_text(msg.message)

async def phone_handler(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    if not re.match(r'^09\d{9}$', phone):
        msg = await get_msg_sync("error1")
        if msg:
            await update.message.reply_text(msg.message)
        return
    telegram_id = update.effective_user.id
    await update_user_phone_sync(telegram_id=telegram_id, phone=phone)
    await show_main_menu(update)

async def show_main_menu(update: Update):
    telegram_id = update.effective_user.id
    if not await user_has_phone_sync(telegram_id):
        msg = await get_msg_sync("error1")
        await update.message.reply_text(msg.message if msg else "شماره موبایل شما ثبت نشده است.")
        return

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
    telegram_id = update.effective_user.id
    if not await user_has_phone_sync(telegram_id):
        msg = await get_msg_sync("error1")
        await update.message.reply_text(msg.message if msg else "شماره موبایل شما ثبت نشده است.")
        return

    products = await get_all_products_sync()
    for product in products:
        images = await sync_to_async(list)(product.images.all())
        if not images:
            continue

        image = images[0]
        image_url = settings.DOMAIN + image.image.url
        caption = f"{product.name}\n{product.description}\n💰 {product.price} تومان\n⚖️ {product.weight} گرم"

        total = len(images)
        inline_buttons = [
            [
                InlineKeyboardButton("▶️", callback_data=f"next_{product.id}_1")
            ] if total > 1 else []
        ]

        back_msg = await get_msg_sync("back_to_menu1")
        inline_buttons.append([
            InlineKeyboardButton(back_msg.message if back_msg else "🔙 بازگشت به منو", callback_data="back_to_menu")
        ])

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image_url,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(inline_buttons)
        )


async def image_slider_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_menu":
        await show_main_menu(update)
        return

    if not (data.startswith("next_") or data.startswith("prev_")):
        return

    action, product_id, index = data.split("_")
    index = int(index)

    product = await get_product_by_id(product_id)
    images = await sync_to_async(list)(product.images.all())
    total = len(images)
    if total == 0:
        return

    if action == "next":
        index = 0 if index >= total else index
    elif action == "prev":
        index = total - 1 if index < 0 else index

    image = images[index]
    image_url = settings.DOMAIN + image.image.url
    caption = f"{product.name}\n{product.description}\n💰 {product.price} تومان\n⚖️ {product.weight} گرم"

    navigation = [
        [
            InlineKeyboardButton("◀️", callback_data=f"prev_{product.id}_{index - 1}"),
            InlineKeyboardButton(f"{index + 1} / {total}", callback_data="noop"),
            InlineKeyboardButton("▶️", callback_data=f"next_{product.id}_{index + 1}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
        ]
    ]

    await query.edit_message_media(
        media=InputMediaPhoto(media=image_url, caption=caption),
        reply_markup=InlineKeyboardMarkup(navigation)
    )
