from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from app.database.models import User, ReadingSession
from app.services.reading_service import remaining_seconds
router = Router()
@router.message(F.text == "⏱ Vaqtim qancha qoldi?")
async def time_left(message: Message, session):
    user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
    if not user: await message.answer("Avval ro‘yxatdan o‘ting."); return
    reading = await session.scalar(select(ReadingSession).where(ReadingSession.user_id == user.id, ReadingSession.status == "active").order_by(ReadingSession.id.desc()))
    if not reading: await message.answer("Faol o‘qish sessiyasi yo‘q."); return
    left = await remaining_seconds(reading)
    await message.answer(f"⏳ Qolgan vaqt: {left} soniya." if left else "✅ Minimal vaqt tugadi. /test buyrug‘ini yuboring.")
