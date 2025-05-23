from telegram import Bot
from telegram.error import TelegramError

CHANNEL_USERNAME = "@tala_faramarzi"  # Your channel username (must be public)

async def has_joined_channel(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError:
        return False


SUPERADMIN_IDS = [185097996, 5455630801] 