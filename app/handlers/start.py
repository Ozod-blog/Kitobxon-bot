import os
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from dotenv import load_dotenv

from app.database.models import User
from app.handlers.registration import Registration
from app.utils.security import is_admin

load_dotenv()
router = Router()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()


def webapp_keyboard():
    if not WEBAPP_URL.startswith("https://"):
        raise ValueError(".env faylida WEBAPP_URL uchun haqiqiy HTTPS manzilini kiriting.")
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📚 Kitobxon WebApp", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session):
    args = (message.text or "").split(maxsplit=1)
    referral_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referral_id = int(args[1][4:])
        except ValueError:
            referral_id = None

    telegram_id = message.from_user.id
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))

    if user:
        if user.is_banned:
            await message.answer("⛔ Akkauntingiz vaqtincha cheklangan. Administrator bilan bog‘laning.")
            return
        await state.clear()
        await message.answer(
            f"Xush kelibsiz, {user.first_name}! 📚\n\nKitobxon platformasini ochish uchun tugmani bosing.",
            reply_markup=webapp_keyboard(),
        )
        return

    if is_admin(telegram_id):
        await state.clear()
        await message.answer(
            "🛠 Xush kelibsiz, administrator!\n\nKitobxon platformasini ochish uchun tugmani bosing.",
            reply_markup=webapp_keyboard(),
        )
        return

    await state.clear()
    await state.update_data(referral_id=referral_id)
    await state.set_state(Registration.first_name)
    await message.answer("📚 Kitobxon Botga xush kelibsiz!\nIsmingizni kiriting:")
