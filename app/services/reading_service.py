from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Book, BookPage, ReadingSession

def utcnow_naive(): return datetime.now(timezone.utc).replace(tzinfo=None)

async def start_reading(session: AsyncSession, user_id: int, book_id: int, page_count: int, seconds_per_page: int):
    book = await session.get(Book, book_id)
    if not book or not book.is_active: raise ValueError("Kitob topilmadi yoki faol emas.")
    if not 1 <= page_count <= book.total_pages: raise ValueError("Sahifalar soni kitob chegarasidan tashqarida.")
    active = await session.scalar(select(ReadingSession).where(ReadingSession.user_id == user_id, ReadingSession.status == "active"))
    if active: raise ValueError("Avvalgi o‘qish sessiyangiz tugatilmagan.")
    obj = ReadingSession(user_id=user_id, book_id=book_id, start_page=1, page_count=page_count,
        started_at=utcnow_naive(), minimum_seconds=page_count * seconds_per_page, status="active")
    session.add(obj); await session.flush(); return obj

async def remaining_seconds(reading: ReadingSession) -> int:
    elapsed = (utcnow_naive() - reading.started_at).total_seconds()
    return max(0, int(reading.minimum_seconds - elapsed))

async def source_for_session(session: AsyncSession, reading: ReadingSession) -> str:
    end_page = reading.start_page + reading.page_count - 1
    pages = (await session.scalars(select(BookPage).where(BookPage.book_id == reading.book_id,
        BookPage.page_number >= reading.start_page, BookPage.page_number <= end_page).order_by(BookPage.page_number))).all()
    if len(pages) != reading.page_count:
        return ""
    return "\n\n".join(f"Sahifa {p.page_number}:\n{p.content}" for p in pages)
