import asyncio, logging
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import get_settings
from app.bot import create_bot
from app.database.engine import engine
from app.database.models import Base
from app.middlewares.database import DatabaseMiddleware
from app.handlers import start, registration
from app.utils.logging import setup_logging

async def main():
    settings=get_settings()
    setup_logging(settings.log_level)
    logger=logging.getLogger(__name__)
    bot=create_bot()
    dp=Dispatcher()
    dp.update.middleware(DatabaseMiddleware())
    for router in [start.router, registration.router]:
        dp.include_router(router)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Kitobxon Bot ishga tushmoqda")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await engine.dispose()
        logger.info("Kitobxon Bot to‘xtadi")

if __name__ == "__main__":
    asyncio.run(main())
