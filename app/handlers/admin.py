import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func
from app.database.models import User, Book, Gift, GiftOrder, AdminAuditLog, BookPage, QuizAttempt, ReadingSession, CoinTransaction, Referral
from app.utils.security import is_admin
from app.services.book_service import add_book, set_page_content
from app.services.gift_service import update_order_status
from app.services.coin_service import change_coins
from app.services.notification_service import broadcast
from app.keyboards.inline import order_keyboard
from app.keyboards.reply import admin_menu, main_menu
router = Router()

class AdminForm(StatesGroup):
    book_title = State()
    book_author = State()
    book_description = State()
    book_pages = State()
    book_pdf = State()
    page_book_id = State()
    page_number = State()
    page_content = State()
    gift_name = State()
    gift_description = State()
    gift_price = State()
    gift_stock = State()
    gift_edit_name = State()
    gift_edit_description = State()
    gift_edit_price = State()
    gift_edit_stock = State()
    coins_telegram_id = State()
    coins_amount = State()
    coins_reason = State()
    broadcast_text = State()
    ban_action = State()
    ban_telegram_id = State()

async def require_admin_message(message: Message) -> bool:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Bu bo‘lim faqat administratorlar uchun.")
        return False
    return True

@router.message(F.text == "🛠 Admin paneli")
async def open_admin_panel(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear()
    await message.answer("🛠 <b>Admin paneli</b>\nKerakli bo‘limni pastdagi tugmalardan tanlang:", reply_markup=admin_menu())

@router.message(F.text == "⬅️ Asosiy menyu")
async def close_admin_panel(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear()
    await message.answer("Asosiy menyu.", reply_markup=main_menu(is_admin=True))

@router.message(F.text == "📊 Statistika")
async def admin_stats_button(message: Message, session):
    if await require_admin_message(message): await send_stats(message, session)

@router.message(F.text == "👥 Foydalanuvchilar")
async def admin_users_button(message: Message, session):
    if await require_admin_message(message): await send_users(message, session)

@router.message(F.text == "📚 Kitoblarni boshqarish")
async def admin_books_button(message: Message, session):
    if not await require_admin_message(message): return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = list((await session.scalars(select(Book).order_by(Book.id.desc()).limit(40))).all())
    if not rows:
        await message.answer("Kitoblar hali qo‘shilmagan.", reply_markup=admin_menu())
        return
    await message.answer("📚 <b>Kitoblarni boshqarish</b>\nHar bir kitobni o‘chirish uchun uning ostidagi 🗑 tugmasini bosing.")
    for b in rows:
        status = "✅ Faol" if b.is_active else "⛔ O‘chirilgan"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🗑 O‘chirish" if b.is_active else "♻️ Qayta faollashtirish",
                                 callback_data=f"admbookdel:{b.id}" if b.is_active else f"admbookrestore:{b.id}")
        ]])
        await message.answer(f"📖 <b>#{b.id} {b.title}</b>\nMuallif: {b.author}\nSahifalar: {b.total_pages}\nHolati: {status}", reply_markup=kb)

@router.callback_query(F.data.startswith("admbookdel:"))
async def admin_book_delete_prompt(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Kitob ID noto‘g‘ri.", show_alert=True)
        return
    book = await session.get(Book, book_id)
    if not book or not book.is_active:
        await callback.answer("Faol kitob topilmadi.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o‘chirish", callback_data=f"admbookconfirm:{book_id}"),
        InlineKeyboardButton(text="↩️ Bekor qilish", callback_data="admbookcancel")
    ]])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer(f"‘{book.title}’ kitobi o‘chirilsinmi?", show_alert=True)

@router.callback_query(F.data.startswith("admbookconfirm:"))
async def admin_book_delete_confirm(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Kitob ID noto‘g‘ri.", show_alert=True)
        return
    book = await session.get(Book, book_id)
    if not book or not book.is_active:
        await callback.answer("Kitob topilmadi yoki allaqachon o‘chirilgan.", show_alert=True)
        return
    book.is_active = False  # soft delete: tarix va o‘qish yozuvlari saqlanadi
    audit(session, callback.from_user.id, "book_deactivate", "book", book.id, book.title)
    await session.commit()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="♻️ Qayta faollashtirish", callback_data=f"admbookrestore:{book.id}")
    ]])
    await callback.message.edit_text(f"🗑 <b>Kitob o‘chirildi</b>\n#{book.id} {book.title} foydalanuvchilar ro‘yxatidan yashirildi. Ma’lumotlar saqlab qolindi.", reply_markup=kb)
    await callback.answer("Kitob o‘chirildi.")

@router.callback_query(F.data.startswith("admbookrestore:"))
async def admin_book_restore(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Kitob ID noto‘g‘ri.", show_alert=True)
        return
    book = await session.get(Book, book_id)
    if not book:
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    book.is_active = True
    audit(session, callback.from_user.id, "book_reactivate", "book", book.id, book.title)
    await session.commit()
    await callback.message.edit_text(f"♻️ <b>Kitob qayta faollashtirildi</b>\n#{book.id} {book.title}")
    await callback.answer("Kitob qayta faollashtirildi.")

@router.callback_query(F.data == "admbookcancel")
async def admin_book_delete_cancel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    await callback.answer("O‘chirish bekor qilindi.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

@router.message(F.text == "➕ Kitob qo‘shish")
async def begin_add_book(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear(); await state.set_state(AdminForm.book_title)
    await message.answer("Kitob nomini yuboring. Bekor qilish uchun /cancel yozing.")

@router.message(AdminForm.book_title)
async def form_book_title(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    if (message.text or '').strip().lower() == '/cancel': await state.clear(); await message.answer('Bekor qilindi.', reply_markup=admin_menu()); return
    if not (message.text or '').strip(): await message.answer('Kitob nomi bo‘sh bo‘lmasin.'); return
    await state.update_data(title=message.text.strip()); await state.set_state(AdminForm.book_author); await message.answer('Muallif ismini yuboring:')

@router.message(AdminForm.book_author)
async def form_book_author(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.update_data(author=(message.text or '').strip()); await state.set_state(AdminForm.book_description); await message.answer('Kitob tavsifini yuboring (tavsif bo‘lmasa - belgisi):')

@router.message(AdminForm.book_description)
async def form_book_description(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.update_data(description='' if (message.text or '').strip() == '-' else (message.text or '').strip()); await state.set_state(AdminForm.book_pdf); await message.answer('Endi kitobning PDF faylini yuboring (Telegram hujjati sifatida). PDF matni sahifalarga ajratib saqlanadi. Bekor qilish: /cancel')

@router.message(F.text == "➕ PDF kitob yuklash")
async def begin_pdf_book(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear()
    await state.set_state(AdminForm.book_title)
    await message.answer("PDF kitob nomini yuboring:")

@router.message(AdminForm.book_pdf)
async def form_book_pdf(message: Message, state: FSMContext, session, bot):
    if not await require_admin_message(message): return
    if (message.text or "").strip().lower() == "/cancel":
        await state.clear(); await message.answer("Bekor qilindi.", reply_markup=admin_menu()); return
    doc = message.document
    if not doc or not (doc.file_name or "").lower().endswith(".pdf") or doc.mime_type not in (None, "application/pdf"):
        await message.answer("Iltimos, PDF faylni Telegram hujjati sifatida yuboring (.pdf).")
        return
    if doc.file_size and doc.file_size > 20 * 1024 * 1024:
        await message.answer("PDF hajmi 20 MB dan oshmasin.")
        return
    import io
    from pypdf import PdfReader
    try:
        buffer = io.BytesIO()
        await bot.download(doc, destination=buffer)
        buffer.seek(0)
        reader = PdfReader(buffer)
        if not reader.pages:
            raise ValueError("PDF sahifalari topilmadi")
        extracted = [(i + 1, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages)]
        if not any(text for _, text in extracted):
            await message.answer("PDF ichidan matn olinmadi. Fayl skan-rasmlardan iborat bo‘lishi mumkin. OCR kerak bo‘ladi.")
            return
        data = await state.get_data()
        book = await add_book(session, data["title"], data["author"], data.get("description", ""), len(extracted))
        for page_no, content in extracted:
            session.add(BookPage(book_id=book.id, page_number=page_no, content=content or "[Bu sahifadan matn olinmadi. PDF faylni ochib ko‘ring.]"))
        await session.flush()
        audit(session, message.from_user.id, "book_pdf_upload", "book", book.id, f"{book.title}; pages={len(extracted)}; file={doc.file_name}")
        await session.commit()
        await state.clear()
        await message.answer(f"✅ PDF kitob saqlandi!\nID: {book.id}\nNomi: {book.title}\nSahifalar: {len(extracted)}\nEndi foydalanuvchilar 📚 Kitoblar bo‘limidan sahifama-sahifa o‘qiy oladi.", reply_markup=admin_menu())
    except Exception as e:
        await session.rollback()
        logging.exception("PDF kitobni yuklashda xato")
        await message.answer(f"PDFni o‘qishda xatolik: {e}. PDF faylni qayta tekshirib yuboring.")

@router.message(AdminForm.book_pages)
async def form_book_pages(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    try: pages=int((message.text or '').strip()); data=await state.get_data(); book=await add_book(session,data['title'],data['author'],data['description'],pages)
    except (ValueError, TypeError) as e: await message.answer(f'Sahifalar soni noto‘g‘ri yoki kitob qo‘shilmadi: {e}'); return
    audit(session,message.from_user.id,'book_create','book',book.id,book.title); await state.clear(); await message.answer(f'✅ Kitob qo‘shildi: #{book.id} {book.title}\nEndi “📄 Sahifa matni qo‘shish” orqali sahifa matnlarini kiriting.',reply_markup=admin_menu())

@router.message(F.text == "📄 Sahifa matni qo‘shish")
async def begin_add_page(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear(); await state.set_state(AdminForm.page_book_id); await message.answer('Kitob ID raqamini yuboring:')

@router.message(AdminForm.page_book_id)
async def form_page_book(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    try: bid=int((message.text or '').strip())
    except ValueError: await message.answer('ID raqam bo‘lishi kerak.'); return
    await state.update_data(book_id=bid); await state.set_state(AdminForm.page_number); await message.answer('Sahifa raqamini yuboring:')

@router.message(AdminForm.page_number)
async def form_page_number(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    try: number=int((message.text or '').strip())
    except ValueError: await message.answer('Sahifa raqami son bo‘lishi kerak.'); return
    await state.update_data(page_number=number); await state.set_state(AdminForm.page_content); await message.answer('Sahifa matnini yuboring:')

@router.message(AdminForm.page_content)
async def form_page_content(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    data=await state.get_data()
    try: await set_page_content(session,data['book_id'],data['page_number'],message.text or '')
    except Exception as e: await message.answer(f'Saqlanmadi: {e}'); return
    audit(session,message.from_user.id,'book_page_upsert','book',data['book_id'],f"page={data['page_number']}"); await state.clear(); await message.answer('✅ Sahifa matni saqlandi.',reply_markup=admin_menu())

@router.message(F.text == "🎁 Sovg‘alarni boshqarish")
async def admin_gifts_button(message: Message, session):
    if not await require_admin_message(message): return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    gifts = list((await session.scalars(select(Gift).order_by(Gift.id.desc()).limit(50))).all())
    if not gifts:
        await message.answer("Hozircha sovg‘alar yo‘q. ➕ Sovg‘a qo‘shish tugmasidan foydalaning.", reply_markup=admin_menu())
        return
    await message.answer("🎁 <b>Sovg‘alarni boshqarish</b>\nSovg‘ani tahrirlash, yashirish yoki qayta faollashtirish uchun tugmasini tanlang.")
    for gift in gifts:
        status = "✅ Faol" if gift.is_active else "⛔ Yashirilgan"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Nomi", callback_data=f"admgiftedit:name:{gift.id}"),
             InlineKeyboardButton(text="📝 Tavsif", callback_data=f"admgiftedit:description:{gift.id}")],
            [InlineKeyboardButton(text="🪙 Narxi", callback_data=f"admgiftedit:price:{gift.id}"),
             InlineKeyboardButton(text="📦 Ombor", callback_data=f"admgiftedit:stock:{gift.id}")],
            [InlineKeyboardButton(text="⛔ Yashirish" if gift.is_active else "♻️ Faollashtirish",
                                  callback_data=f"admgiftactive:{gift.id}")],
            [InlineKeyboardButton(text="🗑️ Butunlay o‘chirish", callback_data=f"admgiftdelete:{gift.id}")]
        ])
        await message.answer(f"🎁 <b>#{gift.id} {gift.name}</b>\nTavsif: {gift.description or '—'}\nNarxi: 🪙 {gift.price}\nOmbor: {gift.stock} dona\nHolati: {status}", reply_markup=kb)

@router.callback_query(F.data.startswith("admgiftdelete:"))
async def admin_gift_delete_confirm(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    try:
        gift_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Sovg‘a ID noto‘g‘ri.", show_alert=True)
        return
    gift = await session.get(Gift, gift_id)
    if not gift:
        await callback.answer("Sovg‘a topilmadi.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o‘chirish", callback_data=f"admgiftdeleteconfirm:{gift.id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admgiftdeletecancel:{gift.id}")
    ]])
    await callback.message.answer(
        f"⚠️ <b>#{gift.id} {gift.name}</b> sovg‘asini butunlay o‘chirmoqchimisiz?\n"
        "Agar ushbu sovg‘a bo‘yicha buyurtmalar mavjud bo‘lsa, tarixni saqlash uchun u butunlay o‘chirilmaydi.",
        reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("admgiftdeletecancel:"))
async def admin_gift_delete_cancel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    await callback.message.edit_text("❌ Sovg‘ani o‘chirish bekor qilindi.")
    await callback.answer()

@router.callback_query(F.data.startswith("admgiftdeleteconfirm:"))
async def admin_gift_delete_do(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True)
        return
    try:
        gift_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Sovg‘a ID noto‘g‘ri.", show_alert=True)
        return
    gift = await session.get(Gift, gift_id)
    if not gift:
        await callback.message.edit_text("Sovg‘a topilmadi yoki avval o‘chirilgan.")
        await callback.answer()
        return
    order_count = await session.scalar(select(func.count(GiftOrder.id)).where(GiftOrder.gift_id == gift_id)) or 0
    if order_count:
        gift.is_active = False
        audit(session, callback.from_user.id, "gift_delete_blocked_archive", "gift", gift.id,
              f"Buyurtmalar tarixi mavjud ({order_count}); sovg‘a yashirildi")
        await session.commit()
        await callback.message.edit_text(
            f"⚠️ #{gift.id} {gift.name} bo‘yicha {order_count} ta buyurtma mavjud.\n"
            "Buyurtmalar tarixi saqlanishi uchun sovg‘a butunlay o‘chirilmaydi; foydalanuvchilardan yashirildi.")
        await callback.answer("Tarix saqlandi, sovg‘a yashirildi.", show_alert=True)
        return
    gift_name = gift.name
    await session.delete(gift)
    audit(session, callback.from_user.id, "gift_delete", "gift", gift_id, gift_name)
    await session.commit()
    await callback.message.edit_text(f"🗑️ #{gift_id} {gift_name} sovg‘asi butunlay o‘chirildi.")
    await callback.answer("Sovg‘a o‘chirildi.")

@router.callback_query(F.data.startswith("admgiftedit:"))
async def admin_gift_edit_start(callback: CallbackQuery, state: FSMContext, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True); return
    try:
        _, field, raw_id = callback.data.split(":", 2); gift_id = int(raw_id)
    except (ValueError, IndexError):
        await callback.answer("So‘rov noto‘g‘ri.", show_alert=True); return
    gift = await session.get(Gift, gift_id)
    if not gift:
        await callback.answer("Sovg‘a topilmadi.", show_alert=True); return
    states = {"name": (AdminForm.gift_edit_name, "Yangi sovg‘a nomini yuboring:"),
              "description": (AdminForm.gift_edit_description, "Yangi tavsifni yuboring (bo‘sh tavsif uchun - yuboring):"),
              "price": (AdminForm.gift_edit_price, "Yangi narxni tanga hisobida yuboring (0 yoki undan katta):"),
              "stock": (AdminForm.gift_edit_stock, "Yangi ombor sonini yuboring (0 yoki undan katta):")}
    if field not in states:
        await callback.answer("Maydon topilmadi.", show_alert=True); return
    await state.clear(); await state.update_data(gift_id=gift.id); await state.set_state(states[field][0])
    await callback.message.answer(f"🎁 #{gift.id} {gift.name}\n{states[field][1]}\nBekor qilish: /cancel")
    await callback.answer()

@router.callback_query(F.data.startswith("admgiftactive:"))
async def admin_gift_toggle_active(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat administratorlar uchun.", show_alert=True); return
    try: gift_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Sovg‘a ID noto‘g‘ri.", show_alert=True); return
    gift = await session.get(Gift, gift_id)
    if not gift:
        await callback.answer("Sovg‘a topilmadi.", show_alert=True); return
    gift.is_active = not gift.is_active
    audit(session, callback.from_user.id, "gift_activate" if gift.is_active else "gift_deactivate", "gift", gift.id, gift.name)
    await session.commit()
    await callback.message.edit_text(f"🎁 <b>#{gift.id} {gift.name}</b>\nHolati: {'✅ Faol' if gift.is_active else '⛔ Yashirilgan'}\nSovg‘a ma’lumotlari va buyurtmalar tarixi saqlandi.")
    await callback.answer("Sovg‘a holati yangilandi.")

async def _save_gift_edit(message: Message, state: FSMContext, session, field: str, value):
    data = await state.get_data(); gift = await session.get(Gift, data.get("gift_id"))
    if not gift:
        await state.clear(); await message.answer("Sovg‘a topilmadi.", reply_markup=admin_menu()); return
    setattr(gift, field, value)
    audit(session, message.from_user.id, "gift_edit", "gift", gift.id, f"{field}={value}")
    await session.commit(); await state.clear()
    await message.answer(f"✅ #{gift.id} {gift.name} yangilandi.", reply_markup=admin_menu())

@router.message(AdminForm.gift_edit_name)
async def form_gift_edit_name(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    value = (message.text or "").strip()
    if not value or value.lower() == "/cancel":
        if value.lower() == "/cancel": await state.clear(); await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        else: await message.answer("Nom bo‘sh bo‘lmasin.")
        return
    await _save_gift_edit(message, state, session, "name", value[:200])

@router.message(AdminForm.gift_edit_description)
async def form_gift_edit_description(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    value = (message.text or "").strip()
    if value.lower() == "/cancel": await state.clear(); await message.answer("Bekor qilindi.", reply_markup=admin_menu()); return
    await _save_gift_edit(message, state, session, "description", "" if value == "-" else value)

@router.message(AdminForm.gift_edit_price)
async def form_gift_edit_price(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    try: value = int((message.text or "").strip()); assert value >= 0
    except (ValueError, AssertionError): await message.answer("Narx 0 yoki undan katta butun son bo‘lishi kerak. /cancel — bekor qilish."); return
    await _save_gift_edit(message, state, session, "price", value)

@router.message(AdminForm.gift_edit_stock)
async def form_gift_edit_stock(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    try: value = int((message.text or "").strip()); assert value >= 0
    except (ValueError, AssertionError): await message.answer("Ombor soni 0 yoki undan katta butun son bo‘lishi kerak. /cancel — bekor qilish."); return
    await _save_gift_edit(message, state, session, "stock", value)

@router.message(F.text == "🎁 Sovg‘a qo‘shish")
async def begin_add_gift(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear(); await state.set_state(AdminForm.gift_name); await message.answer('Sovg‘a nomini yuboring:')

@router.message(AdminForm.gift_name)
async def form_gift_name(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.update_data(name=(message.text or '').strip()); await state.set_state(AdminForm.gift_description); await message.answer('Sovg‘a tavsifini yuboring:')

@router.message(AdminForm.gift_description)
async def form_gift_description(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.update_data(description=(message.text or '').strip()); await state.set_state(AdminForm.gift_price); await message.answer('Narxini tanga hisobida yuboring:')

@router.message(AdminForm.gift_price)
async def form_gift_price(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    try: price=int((message.text or '').strip()); assert price >= 0
    except (ValueError, AssertionError): await message.answer('Narx 0 yoki undan katta butun son bo‘lishi kerak.'); return
    await state.update_data(price=price); await state.set_state(AdminForm.gift_stock); await message.answer('Ombordagi sonini yuboring:')

@router.message(AdminForm.gift_stock)
async def form_gift_stock(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    try:
        stock=int((message.text or '').strip())
        if stock < 0: raise ValueError()
        data=await state.get_data(); gift=Gift(name=data['name'],description=data['description'],price=data['price'],stock=stock)
        session.add(gift); await session.flush(); audit(session,message.from_user.id,'gift_create','gift',gift.id,gift.name)
    except (ValueError, TypeError): await message.answer('Ombor soni 0 yoki undan katta butun son bo‘lishi kerak.'); return
    await state.clear(); await message.answer(f'✅ Sovg‘a qo‘shildi: #{gift.id} {gift.name}',reply_markup=admin_menu())

@router.message(F.text == "🧾 Buyurtmalar")
async def admin_orders_button(message: Message, session):
    if not await require_admin_message(message): return
    await send_orders(message,session)

@router.message(F.text == "🪙 Tangalarni boshqarish")
async def begin_coin_adjustment(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear(); await state.set_state(AdminForm.coins_telegram_id); await message.answer('Foydalanuvchining Telegram ID raqamini yuboring:')

@router.message(AdminForm.coins_telegram_id)
async def form_coins_id(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    try: uid=int((message.text or '').strip())
    except ValueError: await message.answer('Telegram ID raqam bo‘lishi kerak.'); return
    await state.update_data(telegram_id=uid); await state.set_state(AdminForm.coins_amount); await message.answer('Tanga miqdorini yuboring. Qo‘shish uchun musbat, ayirish uchun manfiy son:')

@router.message(AdminForm.coins_amount)
async def form_coins_amount(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    try: amount=int((message.text or '').strip())
    except ValueError: await message.answer('Miqdor butun son bo‘lishi kerak.'); return
    await state.update_data(amount=amount); await state.set_state(AdminForm.coins_reason); await message.answer('Operatsiya sababini yozing:')

@router.message(AdminForm.coins_reason)
async def form_coins_reason(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    data=await state.get_data()
    try:
        target=await session.scalar(select(User).where(User.telegram_id==data['telegram_id']))
        if not target: raise ValueError('Foydalanuvchi topilmadi.')
        await change_coins(session,target.id,data['amount'],'admin_adjustment',(message.text or '')[:250],f"admin-ui:{message.from_user.id}:{target.id}:{message.message_id}")
        audit(session,message.from_user.id,'coin_adjustment','user',target.id,f"amount={data['amount']};reason={message.text}")
    except Exception as e: await message.answer(f'Amal bajarilmadi: {e}'); return
    await state.clear(); await message.answer(f'✅ Balans yangilandi: {target.coins} tanga.',reply_markup=admin_menu())

@router.message(F.text == "📣 Xabar yuborish")
async def begin_broadcast(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear(); await state.set_state(AdminForm.broadcast_text); await message.answer('Barcha ban qilinmagan foydalanuvchilarga yuboriladigan xabar matnini kiriting:')

@router.message(AdminForm.broadcast_text)
async def form_broadcast(message: Message, state: FSMContext, session, bot):
    if not await require_admin_message(message): return
    body=(message.text or '').strip()
    if not body: await message.answer('Xabar bo‘sh bo‘lmasin.'); return
    ids=list((await session.scalars(select(User.telegram_id).where(User.is_banned.is_(False)))).all())
    sent,failed=await broadcast(bot,ids,body); audit(session,message.from_user.id,'broadcast','users','all',f'sent={sent};failed={failed}')
    await state.clear(); await message.answer(f'📣 Yuborildi: {sent}; xato: {failed}',reply_markup=admin_menu())

@router.message(F.text == "🚫 BAN boshqaruvi")
async def begin_ban_management(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear(); await state.set_state(AdminForm.ban_action); await message.answer('Amalni tanlab yozing: ban yoki unban')

@router.message(AdminForm.ban_action)
async def form_ban_action(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    action=(message.text or '').strip().lower()
    if action not in {'ban','unban'}: await message.answer('Faqat ban yoki unban deb yozing.'); return
    await state.update_data(action=action); await state.set_state(AdminForm.ban_telegram_id); await message.answer('Foydalanuvchining Telegram ID raqamini yuboring:')

@router.message(AdminForm.ban_telegram_id)
async def form_ban_user(message: Message, state: FSMContext, session):
    if not await require_admin_message(message): return
    try: uid=int((message.text or '').strip())
    except ValueError: await message.answer('Telegram ID raqam bo‘lishi kerak.'); return
    user=await session.scalar(select(User).where(User.telegram_id==uid))
    if not user: await message.answer('Foydalanuvchi topilmadi.'); return
    data=await state.get_data(); user.is_banned=(data['action']=='ban'); audit(session,message.from_user.id,data['action'],'user',user.id)
    await state.clear(); await message.answer(f"✅ {uid}: {'BAN qilindi' if user.is_banned else 'BAN olib tashlandi'}.",reply_markup=admin_menu())

def audit(session, admin_id, action, target_type, target_id, details=""):
    session.add(AdminAuditLog(admin_telegram_id=admin_id, action=action, target_type=target_type, target_id=str(target_id), details=details[:1000]))

@router.message(Command("cancel"))
async def cancel_admin_action(message: Message, state: FSMContext):
    if not await require_admin_message(message): return
    await state.clear()
    await message.answer("Amal bekor qilindi.", reply_markup=admin_menu())

@router.message(Command("admin"))
async def admin_home(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    await state.clear()
    await message.answer("🛠 Admin paneli\nKerakli bo‘limni pastdagi tugmalardan tanlang:", reply_markup=admin_menu())

@router.message(Command("addbook"))
async def addbook_cmd(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    parts=(message.text or "").split("|")
    if len(parts)!=5: await message.answer("Format: /addbook|Nomi|Muallif|Tavsif|Sahifalar"); return
    try:
        book=await add_book(session,parts[1],parts[2],parts[3],int(parts[4]))
        audit(session,message.from_user.id,"book_create","book",book.id,book.title)
        await message.answer(f"Kitob qo‘shildi: #{book.id} {book.title}")
    except Exception as e: await message.answer(f"Kitob qo‘shilmadi: {e}")

@router.message(Command("addpage"))
async def addpage_cmd(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    parts=(message.text or "").split(maxsplit=3)
    if len(parts)<4: await message.answer("Format: /addpage BOOK_ID PAGE MATN"); return
    try:
        await set_page_content(session,int(parts[1]),int(parts[2]),parts[3])
        audit(session,message.from_user.id,"book_page_upsert","book",parts[1],f"page={parts[2]}")
        await message.answer("Sahifa matni saqlandi.")
    except Exception as e: await message.answer(f"Saqlanmadi: {e}")

@router.message(Command("addgift"))
async def addgift_cmd(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    parts=(message.text or "").split("|")
    if len(parts)!=5: await message.answer("Format: /addgift|Nomi|Tavsif|Narx|Ombor"); return
    try:
        gift=Gift(name=parts[1],description=parts[2],price=int(parts[3]),stock=int(parts[4]))
        if gift.price < 0 or gift.stock < 0: raise ValueError("Narx va ombor manfiy bo‘lmasin.")
        session.add(gift); await session.flush()
        audit(session,message.from_user.id,"gift_create","gift",gift.id,gift.name)
        await message.answer(f"Sovg‘a qo‘shildi: #{gift.id}")
    except Exception as e: await message.answer(f"Sovg‘a qo‘shilmadi: {e}")

async def send_orders(message: Message, session):
    orders=list((await session.scalars(select(GiftOrder).where(GiftOrder.status=="pending").order_by(GiftOrder.created_at).limit(50))).all())
    if not orders: await message.answer("Kutilayotgan buyurtmalar yo‘q."); return
    for o in orders: await message.answer(f"Buyurtma #{o.id} | user_id={o.user_id} | gift_id={o.gift_id} | narx={o.price_each}",reply_markup=order_keyboard(o.id))

@router.message(Command("orders"))
async def orders(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    await send_orders(message, session)

@router.callback_query(F.data.startswith("order:"))
async def order_action(callback: CallbackQuery, session):
    if not is_admin(callback.from_user.id): await callback.answer("Ruxsat yo‘q.",show_alert=True); return
    try: _,status,oid=callback.data.split(":"); oid=int(oid)
    except ValueError: await callback.answer("Noto‘g‘ri so‘rov.",show_alert=True); return
    try:
        order=await update_order_status(session,oid,status)
        audit(session,callback.from_user.id,"gift_order_status","gift_order",oid,status)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer(f"Buyurtma: {order.status}")
    except Exception as e: await callback.answer(str(e),show_alert=True)

async def send_stats(message: Message, session):
    users=await session.scalar(select(func.count(User.id))) or 0
    pages=await session.scalar(select(func.coalesce(func.sum(User.total_pages),0))) or 0
    quizzes=await session.scalar(select(func.count(QuizAttempt.id))) or 0
    coins=await session.scalar(select(func.coalesce(func.sum(CoinTransaction.amount),0))) or 0
    refs=await session.scalar(select(func.count(Referral.id))) or 0
    orders=await session.scalar(select(func.count(GiftOrder.id))) or 0
    await message.answer(f"📊 Hisobot\nFoydalanuvchilar: {users}\nO‘qilgan sahifalar: {pages}\nTest urinishlari: {quizzes}\nTanga operatsiyalari netto: {coins}\nReferral: {refs}\nSovg‘a buyurtmalari: {orders}")

async def send_users(message: Message, session):
    rows=list((await session.scalars(select(User).order_by(User.id.desc()).limit(30))).all())
    await message.answer("\n".join(f"{u.id} | tg={u.telegram_id} | {u.first_name} {u.last_name} | coins={u.coins} | banned={u.is_banned}" for u in rows) or "Foydalanuvchilar yo‘q.")

@router.message(Command("stats"))
async def stats(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    await send_stats(message, session)

@router.message(Command("users"))
async def users(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    await send_users(message, session)

@router.message(Command("coins"))
async def coins(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    p=(message.text or "").split(maxsplit=3)
    if len(p)<4: await message.answer("Format: /coins TELEGRAM_ID MIQDOR SABAB"); return
    try:
        target=await session.scalar(select(User).where(User.telegram_id==int(p[1])))
        if not target: raise ValueError("Foydalanuvchi topilmadi.")
        amount=int(p[2])
        await change_coins(session,target.id,amount,"admin_adjustment",p[3],f"admin:{message.from_user.id}:{target.id}:{message.message_id}")
        audit(session,message.from_user.id,"coin_adjustment","user",target.id,f"amount={amount};reason={p[3]}")
        await message.answer(f"Balans yangilandi: {target.coins} tanga.")
    except Exception as e: await message.answer(f"Amal bajarilmadi: {e}")

@router.message(Command("ban"))
async def ban(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    p=(message.text or "").split()
    if len(p)!=2: await message.answer("Format: /ban TELEGRAM_ID"); return
    user=await session.scalar(select(User).where(User.telegram_id==int(p[1])))
    if not user: await message.answer("Foydalanuvchi topilmadi."); return
    user.is_banned=True; audit(session,message.from_user.id,"ban","user",user.id); await message.answer("Foydalanuvchi BAN qilindi.")

@router.message(Command("unban"))
async def unban(message: Message, session):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    p=(message.text or "").split()
    if len(p)!=2: await message.answer("Format: /unban TELEGRAM_ID"); return
    user=await session.scalar(select(User).where(User.telegram_id==int(p[1])))
    if not user: await message.answer("Foydalanuvchi topilmadi."); return
    user.is_banned=False; audit(session,message.from_user.id,"unban","user",user.id); await message.answer("BAN olib tashlandi.")

@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message, session, bot):
    if not is_admin(message.from_user.id): await message.answer("Ruxsat yo‘q."); return
    body=(message.text or "").partition(" ")[2].strip()
    if not body: await message.answer("Format: /broadcast Xabar matni"); return
    ids=list((await session.scalars(select(User.telegram_id).where(User.is_banned.is_(False)))).all())
    sent,failed=await broadcast(bot,ids,body)
    audit(session,message.from_user.id,"broadcast","users","all",f"sent={sent};failed={failed}")
    await message.answer(f"Yuborildi: {sent}; xato: {failed}")
