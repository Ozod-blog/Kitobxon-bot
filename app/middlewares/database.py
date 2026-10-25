from aiogram import BaseMiddleware
from app.database.engine import SessionFactory
class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with SessionFactory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
