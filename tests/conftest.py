import os
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN_NOT_REAL")
os.environ.setdefault("AI_PROVIDER", "gemini")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("ADMIN_IDS", "999")
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database.models import Base
@pytest.fixture
async def session(tmp_path):
    engine=create_async_engine(f"sqlite+aiosqlite:///{tmp_path/'test.db'}")
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with factory() as s:
        yield s
        await s.rollback()
    await engine.dispose()
