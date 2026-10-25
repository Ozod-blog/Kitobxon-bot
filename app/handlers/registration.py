from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardRemove
from dotenv import load_dotenv
import os

from app.services.user_service import register_user
from app.services.referral_service import attach_referral
from app.keyboards.reply import contact_keyboard
from app.utils.validators import valid_person_name, valid_phone

load_dotenv()
router = Router()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()


def webapp_keyboard():
    if not WEBAPP_URL.startswith("https://"):
        raise ValueError(".env faylida WEBAPP_URL uchun haqiqiy HTTPS manzilini kiriting.")
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📚 Kitobxon WebApp", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])


class Registration(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    region = State()
    district = State()


@router.message(Command("cancel"))
@router.message(F.text == "❌ Bekor qilish")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ro‘yxatdan o‘tish bekor qilindi. Davom etish uchun /start bosing.")


@router.message(Registration.first_name)
async def first_name(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not valid_person_name(value):
        await message.answer("Ismni to‘g‘ri kiriting (2–80 belgi).")
        return
    await state.update_data(first_name=value)
    await state.set_state(Registration.last_name)
    await message.answer("Familiyangizni kiriting:")


@router.message(Registration.last_name)
async def last_name(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not valid_person_name(value):
        await message.answer("Familiyani to‘g‘ri kiriting (2–80 belgi).")
        return
    await state.update_data(last_name=value)
    await state.set_state(Registration.phone)
    await message.answer("Telefon raqamingizni pastdagi tugma orqali yuboring:", reply_markup=contact_keyboard())


@router.message(Registration.phone)
async def phone(message: Message, state: FSMContext):
    contact = message.contact
    if not contact or contact.user_id != message.from_user.id:
        await message.answer("Xavfsizlik uchun faqat o‘zingizning Telegram kontaktingizni tugma orqali yuboring.")
        return
    if not valid_phone(contact.phone_number):
        await message.answer("Telefon raqami noto‘g‘ri ko‘rinadi. Qayta yuboring.")
        return
    await state.update_data(phone=contact.phone_number)
    await state.set_state(Registration.region)
    await message.answer("Viloyatingizni kiriting:", reply_markup=ReplyKeyboardRemove())


@router.message(Registration.region)
async def region(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not 2 <= len(value) <= 100:
        await message.answer("Viloyat nomini 2–100 belgi oralig‘ida kiriting.")
        return
    await state.update_data(region=value)
    await state.set_state(Registration.district)
    await message.answer("Shahar yoki tumaningizni kiriting:")


@router.message(Registration.district)
async def district(message: Message, state: FSMContext, session):
    value = (message.text or "").strip()
    if not 2 <= len(value) <= 100:
        await message.answer("Shahar/tuman nomini 2–100 belgi oralig‘ida kiriting.")
        return
    data = await state.get_data()
    referral_id = data.get("referral_id")
    try:
        user = await register_user(
            session,
            telegram_id=message.from_user.id,
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data["phone"],
            region=data["region"],
            district=value,
        )
        await attach_referral(session, user, referral_id)
    except ValueError as e:
        await message.answer(str(e))
        return

    await state.clear()
    await message.answer(
        "✅ Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi!\n\nKitobxon platformasini ochish uchun tugmani bosing.",
        reply_markup=webapp_keyboard(),
    )
