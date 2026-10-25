from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select, func, desc
from app.database.models import User, Book, Gift, ReadingSession, Quiz, QuizAttempt, Referral, CoinTransaction
from app.keyboards.reply import main_menu
from app.utils.security import is_admin
router = Router()

@router.message(F.text == "ℹ️ Yordam")
async def help_message(message: Message):
    await message.answer("📚 Kitob tanlang, o‘qish sessiyasini boshlang va minimal vaqt o‘tgach test topshiring.\nHar sessiya uchun test bir marta topshiriladi. Matn biriktirilmagan sahifalar uchun test yaratib bo‘lmaydi.")

@router.message(F.text == "📚 Kitoblar")
async def books(message: Message, session):
    items = list((await session.scalars(select(Book).where(Book.is_active.is_(True)).order_by(Book.title).limit(30))).all())
    if not items: await message.answer("Hozircha kitoblar mavjud emas."); return
    from app.keyboards.inline import books_keyboard
    await message.answer("📚 O‘qish uchun kitobni tanlang:", reply_markup=books_keyboard(items, "viewbook"))

@router.message(F.text == "👤 Mening profilim")
async def profile(message: Message, session):
    user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
    if not user: await message.answer("Avval /start orqali ro‘yxatdan o‘ting."); return
    tests = await session.scalar(select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == user.id)) or 0
    passed = await session.scalar(select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == user.id, QuizAttempt.passed.is_(True))) or 0
    refs = await session.scalar(select(func.count(Referral.id)).where(Referral.inviter_id == user.id)) or 0
    rewards = await session.scalar(select(func.coalesce(func.sum(CoinTransaction.amount),0)).where(CoinTransaction.user_id == user.id, CoinTransaction.operation_type.like("referral%"))) or 0
    await message.answer(f"👤 {user.first_name} {user.last_name}\n📱 {user.phone}\n📍 {user.region}, {user.district}\n🆔 {user.telegram_id}\n🪙 Tangalar: {user.coins}\n📖 O‘qilgan sahifalar: {user.total_pages}\n📝 Testlar: {tests} (muvaffaqiyatli: {passed})\n👥 Takliflar: {refs}\n🪙 Referral tangalari: {rewards}")

@router.message(F.text == "🏆 Reyting")
async def leaderboard(message: Message, session):
    users = list((await session.scalars(select(User).where(User.is_banned.is_(False)).order_by(desc(User.coins), desc(User.total_pages), User.id).limit(50))).all())
    if not users: await message.answer("Reyting hozircha bo‘sh."); return
    rank = next((i for i,u in enumerate(users,1) if u.telegram_id == message.from_user.id), None)
    lines = ["🏆 TOP 50"]
    lines += [f"{i}. {u.first_name} {u.last_name} — 🪙 {u.coins} | 📖 {u.total_pages} sahifa" for i,u in enumerate(users,1)]
    lines.append(f"\nSizning o‘rningiz: {rank if rank else 'TOP 50 dan tashqarida'}")
    await message.answer("\n".join(lines))

@router.message(F.text == "👥 Do‘stlarni taklif qilish")
async def referrals(message: Message, session):
    user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
    if not user: await message.answer("Avval ro‘yxatdan o‘ting."); return
    from app.config import get_settings
    s = get_settings()
    username = s.bot_username.lstrip("@")
    if not username:
        await message.answer("BOT_USERNAME .env faylida sozlanmagan. Bot administratoriga xabar bering."); return
    count = await session.scalar(select(func.count(Referral.id)).where(Referral.inviter_id == user.id)) or 0
    earned = await session.scalar(select(func.coalesce(func.sum(CoinTransaction.amount),0)).where(CoinTransaction.user_id == user.id, CoinTransaction.operation_type.like("referral%"))) or 0
    await message.answer(f"👥 Shaxsiy havolangiz:\nhttps://t.me/{username}?start=ref_{user.telegram_id}\n\nTakliflar: {count}\nReferral orqali olingan tangalar: {earned}\nMukofot qoidasi: sozlamaga ko‘ra ro‘yxatdan o‘tishda yoki do‘stning birinchi muvaffaqiyatli testida.")

@router.message(F.text == "📖 O‘qishni boshlash")
async def start_reading_menu(message: Message, session):
    from app.keyboards.inline import books_keyboard
    items = list((await session.scalars(select(Book).where(Book.is_active.is_(True)).order_by(Book.title).limit(30))).all())
    if not items: await message.answer("Hozircha kitoblar mavjud emas."); return
    await message.answer("O‘qimoqchi bo‘lgan kitobni tanlang:", reply_markup=books_keyboard(items, "readbook"))
