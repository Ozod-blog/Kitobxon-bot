from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Book, Gift

class UserRepository:
    def __init__(self, session: AsyncSession): self.session = session
    async def by_telegram_id(self, telegram_id: int):
        return await self.session.scalar(select(User).where(User.telegram_id == telegram_id))
    async def create(self, **kwargs):
        obj = User(**kwargs); self.session.add(obj); await self.session.flush(); return obj

class BookRepository:
    def __init__(self, session: AsyncSession): self.session = session
    async def active(self):
        return list((await self.session.scalars(select(Book).where(Book.is_active.is_(True)).order_by(Book.title))).all())
    async def search(self, term: str):
        return list((await self.session.scalars(select(Book).where(Book.is_active.is_(True), Book.title.ilike(f"%{term}%")).order_by(Book.title).limit(30))).all())

class GiftRepository:
    def __init__(self, session: AsyncSession): self.session = session
    async def active(self):
        return list((await self.session.scalars(select(Gift).where(Gift.is_active.is_(True), Gift.stock > 0).order_by(Gift.price))).all())
