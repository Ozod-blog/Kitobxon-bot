from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings

settings = get_settings()

def _engine_args():
    url = make_url(settings.database_url)
    kwargs = {"echo": False, "pool_pre_ping": True}
    if url.drivername.startswith("postgresql"):
        # asyncpg "sslmode" va "channel_binding" parametrlarini tanimaydi: olib tashlab, ssl=True beramiz.
        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        ssl = query.pop("ssl", None)
        query.pop("channel_binding", None)
        url = url.set(query=query)
        wants_ssl = (sslmode or ssl or "") not in ("", "disable", "false")
        kwargs["connect_args"] = {"ssl": True} if wants_ssl else {}
        kwargs["pool_recycle"] = 300      # bulutli bazalar bo‘sh ulanishlarni uzib qo‘yadi
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 5
    return url, kwargs

_url, _kwargs = _engine_args()
engine = create_async_engine(_url, **_kwargs)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
