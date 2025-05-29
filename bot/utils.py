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


from PIL import Image
from io import BytesIO
import os

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB

def resize_image_from_path(path: str) -> BytesIO | None:
    try:
        if not os.path.exists(path):
            return None

        with open(path, 'rb') as f:
            data = f.read()

        # If already small enough
        if len(data) <= MAX_PHOTO_SIZE:
            return BytesIO(data)

        img = Image.open(BytesIO(data))
        img_format = img.format if img.format else "JPEG"

        for quality in range(85, 10, -5):
            buffer = BytesIO()
            img.save(buffer, format=img_format, optimize=True, quality=quality)
            if buffer.tell() <= MAX_PHOTO_SIZE:
                buffer.seek(0)
                return buffer

        return None
    except Exception as e:
        print(f"Resize error: {e}")
        return None


