from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def books_keyboard(books, prefix="book"):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{b.title} — {b.author}", callback_data=f"{prefix}:{b.id}")] for b in books])
def quiz_option_keyboard(quiz_id: int, question_id: int, options: list[str]):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{i+1}. {opt[:45]}", callback_data=f"ans:{quiz_id}:{question_id}:{i}")] for i,opt in enumerate(options)])
def order_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"order:approved:{order_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"order:rejected:{order_id}")]])


def book_page_keyboard(book_id: int, page_number: int, total_pages: int):
    row = []
    if page_number > 1:
        row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{book_id}:{page_number-1}"))
    if page_number < total_pages:
        row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page:{book_id}:{page_number+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[row] if row else [[InlineKeyboardButton(text="📚 Kitoblar", callback_data="backbooks")]])
