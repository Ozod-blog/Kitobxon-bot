import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
logger = logging.getLogger(__name__)

async def broadcast(bot: Bot, telegram_ids: list[int], text: str, photo_file_id: str | None = None, button_url: str | None = None):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Havolani ochish", url=button_url)]]) if button_url else None
    sent = failed = 0
    for uid in telegram_ids:
        try:
            if photo_file_id:
                await bot.send_photo(uid, photo_file_id, caption=text, reply_markup=markup)
            else:
                await bot.send_message(uid, text, reply_markup=markup)
            sent += 1
        except TelegramForbiddenError:
            failed += 1
            logger.info("Broadcast recipient blocked bot: %s", uid)
        except TelegramAPIError:
            failed += 1
            logger.exception("Broadcast send failed for telegram_id=%s", uid)
        await asyncio.sleep(0.05)
    return sent, failed
