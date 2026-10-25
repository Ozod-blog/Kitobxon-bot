from aiogram import Bot
from app.config import get_settings
def create_bot():
    return Bot(token=get_settings().bot_token)
