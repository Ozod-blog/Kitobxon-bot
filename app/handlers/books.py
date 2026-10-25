import html
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from app.database.models import Book, User
from app.services.reading_service import start_reading, remaining_seconds
from app.config import get_settings
router = Router()

@router.callback_query(F.data.startswith("viewbook:"))
async def view_book(callback: CallbackQuery, session):
    try: book_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Kitob ID noto‘g‘ri", show_alert=True); return
    book = await session.get(Book, book_id)
    if not book or not book.is_active:
        await callback.answer("Kitob mavjud emas", show_alert=True); return
    from app.database.models import BookPage
    from app.keyboards.inline import book_page_keyboard
    page = await session.scalar(select(BookPage).where(BookPage.book_id == book_id, BookPage.page_number == 1))
    if not page:
        await callback.message.answer("Bu kitob uchun sahifa matni topilmadi. Administrator PDF yuklashi kerak.")
    else:
        body = html.escape((page.content or "Bu sahifada matn yo‘q.")[:2800])
        await callback.message.answer(f"📖 <b>{html.escape(book.title)}</b> — {html.escape(book.author)}\nSahifa 1/{book.total_pages}\n\n{body}", reply_markup=book_page_keyboard(book.id, 1, book.total_pages))
    await callback.answer()

@router.callback_query(F.data.startswith("page:"))
async def show_book_page(callback: CallbackQuery, session):
    try: _, raw_book, raw_page = callback.data.split(":", 2); book_id, page_no = int(raw_book), int(raw_page)
    except (ValueError, TypeError):
        await callback.answer("Sahifa raqami noto‘g‘ri", show_alert=True); return
    book = await session.get(Book, book_id)
    if not book or not book.is_active or not 1 <= page_no <= book.total_pages:
        await callback.answer("Sahifa topilmadi", show_alert=True); return
    from app.database.models import BookPage
    from app.keyboards.inline import book_page_keyboard
    page = await session.scalar(select(BookPage).where(BookPage.book_id == book_id, BookPage.page_number == page_no))
    if not page:
        await callback.answer("Bu sahifaning matni topilmadi", show_alert=True); return
    body = html.escape((page.content or "Bu sahifada matn yo‘q.")[:2800])
    text = f"📖 <b>{html.escape(book.title)}</b> — {html.escape(book.author)}\nSahifa {page_no}/{book.total_pages}\n\n{body}"
    try:
        await callback.message.edit_text(text, reply_markup=book_page_keyboard(book.id, page_no, book.total_pages))
    except Exception:
        await callback.message.answer(text, reply_markup=book_page_keyboard(book.id, page_no, book.total_pages))
    await callback.answer()

@router.callback_query(F.data == "backbooks")
async def back_to_books(callback: CallbackQuery, session):
    items = list((await session.scalars(select(Book).where(Book.is_active.is_(True)).order_by(Book.title).limit(30))).all())
    from app.keyboards.inline import books_keyboard
    await callback.message.answer("📚 Kitobni tanlang:", reply_markup=books_keyboard(items, "viewbook"))
    await callback.answer()

class ReadingInput(StatesGroup):
    page_count = State()

@router.callback_query(F.data.startswith("readbook:"))
async def choose_book(callback: CallbackQuery, state: FSMContext, session):
    book_id = int(callback.data.split(":")[1])
    book = await session.get(Book, book_id)
    if not book or not book.is_active:
        await callback.answer("Kitob mavjud emas.", show_alert=True); return
    await state.update_data(book_id=book_id)
    await state.set_state(ReadingInput.page_count)
    await callback.message.answer(f"{book.title}: nechta sahifa o‘qimoqchisiz? (1–{book.total_pages})")
    await callback.answer()

@router.message(ReadingInput.page_count)
async def enter_pages(message: Message, state: FSMContext, session):
    try: pages = int((message.text or "").strip())
    except ValueError:
        await message.answer("Sahifalar sonini butun son bilan kiriting."); return
    data = await state.get_data()
    user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
    if not user: await message.answer("Avval ro‘yxatdan o‘ting."); return
    try:
        reading = await start_reading(session, user.id, data["book_id"], pages, get_settings().min_seconds_per_page)
    except ValueError as e:
        await message.answer(str(e)); return
    await state.clear()
    await message.answer(f"⏱ O‘qish boshlandi. Sessiya #{reading.id}\nSahifalar: {pages}\nMinimal vaqt: {reading.minimum_seconds} soniya.\nVaqt serverda saqlanadi. Vaqt tugagach /test buyrug‘i orqali test yarating.")

@router.message(F.text == "/test")
async def begin_test_command(message: Message, session, state):
    user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
    if not user: await message.answer("Avval ro‘yxatdan o‘ting."); return
    from app.database.models import ReadingSession
    active = await session.scalar(select(ReadingSession).where(ReadingSession.user_id == user.id, ReadingSession.status == "active").order_by(ReadingSession.id.desc()))
    if not active: await message.answer("Faol o‘qish sessiyasi topilmadi."); return
    remaining = await remaining_seconds(active)
    if remaining:
        await message.answer(f"⏳ Test boshlash uchun yana {remaining} soniya kuting."); return
    from app.handlers.quiz import launch_quiz
    await launch_quiz(message, session, user, active, state)
