from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from app.database.models import Gift, User
from app.services.gift_service import create_order
router = Router()
@router.message(F.text == "🎁 Sovg‘alar bozori")
async def market(message: Message, session):
    gifts = list((await session.scalars(select(Gift).where(Gift.is_active.is_(True), Gift.stock > 0).order_by(Gift.price))).all())
    if not gifts: await message.answer("Hozircha mavjud sovg‘alar yo‘q."); return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{g.name} — 🪙 {g.price} ({g.stock} dona)", callback_data=f"gift:{g.id}")] for g in gifts])
    await message.answer("🎁 Sovg‘alar bozori:", reply_markup=kb)

@router.callback_query(F.data.startswith("gift:"))
async def select_gift(callback: CallbackQuery, session):
    try: gift_id = int(callback.data.split(":")[1])
    except ValueError: await callback.answer("Noto‘g‘ri sovg‘a.", show_alert=True); return
    gift = await session.get(Gift, gift_id)
    user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
    if not gift or not gift.is_active or gift.stock < 1 or not user:
        await callback.answer("Sovg‘a mavjud emas yoki foydalanuvchi ro‘yxatdan o‘tmagan.", show_alert=True); return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Buyurtmani tasdiqlash", callback_data=f"giftbuy:{gift.id}")]])
    await callback.message.answer(f"{gift.name}\n{gift.description}\nNarxi: {gift.price} tanga\nBalansingiz: {user.coins}", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("giftbuy:"))
async def buy_gift(callback: CallbackQuery, session, bot):
    try: gift_id = int(callback.data.split(":")[1])
    except ValueError: await callback.answer("Noto‘g‘ri so‘rov.", show_alert=True); return
    user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
    if not user: await callback.answer("Avval ro‘yxatdan o‘ting.", show_alert=True); return
    try:
        order = await create_order(session, user.id, gift_id)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True); return
    from app.config import get_settings
    from app.keyboards.inline import order_keyboard
    for admin_id in get_settings().admin_ids:
        try: await bot.send_message(admin_id, f"🎁 Yangi buyurtma #{order.id}\nFoydalanuvchi: {user.telegram_id}\nSovg‘a ID: {gift_id}", reply_markup=order_keyboard(order.id))
        except Exception: pass
    await callback.message.answer(f"Buyurtma #{order.id} yaratildi. Tangalar rezerv qilindi; administrator javobini kuting.")
    await callback.answer()
