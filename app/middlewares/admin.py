from aiogram import BaseMiddleware
from app.utils.security import is_admin
class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user or not is_admin(user.id):
            return None
        return await handler(event, data)
