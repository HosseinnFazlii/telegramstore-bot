from telegram import Bot
from telegram.error import TelegramError

CHANNEL_USERNAME = "@tala_faramarzi"  # Your channel username (must be public)

async def has_joined_channel(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError:
        return False


SUPERADMIN_IDS = [185097996, 5455630801,5532532535] 


import aiohttp
from PIL import Image
from io import BytesIO

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB in bytes

async def fetch_and_resize_image(url: str) -> BytesIO | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                data = await response.read()

        # If already under 5MB, return as-is
        if len(data) <= MAX_PHOTO_SIZE:
            return BytesIO(data)

        # Else resize
        img = Image.open(BytesIO(data))
        img_format = img.format if img.format else "JPEG"

        # Resize loop — try reducing quality until it fits
        for quality in range(85, 10, -5):
            buffer = BytesIO()
            img.save(buffer, format=img_format, optimize=True, quality=quality)
            if buffer.tell() <= MAX_PHOTO_SIZE:
                buffer.seek(0)
                return buffer

        return None  # Couldn’t compress enough

    except Exception as e:
        print(f"Image resize error: {e}")
        return None


