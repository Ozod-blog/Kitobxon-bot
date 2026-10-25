from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User

async def register_user(session: AsyncSession, **data) -> User:
    existing = await session.scalar(select(User).where(User.telegram_id == data["telegram_id"]))
    if existing: raise ValueError("Bu Telegram akkaunti avval ro‘yxatdan o‘tgan.")
    existing_phone = await session.scalar(select(User).where(User.phone == data["phone"]))
    if existing_phone: raise ValueError("Bu telefon raqami boshqa akkauntga biriktirilgan.")
    user = User(**data)
    session.add(user)
    await session.flush()
    return user
