from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Book, BookPage

async def list_books(session: AsyncSession, search: str = ""):
    stmt = select(Book).where(Book.is_active.is_(True))
    if search: stmt = stmt.where(Book.title.ilike(f"%{search}%"))
    return list((await session.scalars(stmt.order_by(Book.title).limit(30))).all())

async def add_book(session: AsyncSession, title: str, author: str, description: str, total_pages: int):
    if total_pages < 1: raise ValueError("Sahifalar soni kamida 1 bo‘lishi kerak.")
    book = Book(title=title.strip(), author=author.strip(), description=description.strip(), total_pages=total_pages)
    session.add(book); await session.flush(); return book

async def set_page_content(session: AsyncSession, book_id: int, page_number: int, content: str):
    book = await session.get(Book, book_id)
    if not book or not 1 <= page_number <= book.total_pages: raise ValueError("Kitob yoki sahifa raqami noto‘g‘ri.")
    page = await session.scalar(select(BookPage).where(BookPage.book_id == book_id, BookPage.page_number == page_number))
    if page: page.content = content
    else: session.add(BookPage(book_id=book_id, page_number=page_number, content=content))
    await session.flush()
