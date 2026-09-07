from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from bot.config import Settings
from bot.db.models import Base

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_sqlite_dir(url: str) -> None:
    if "sqlite" not in url:
        return
    # sqlite+aiosqlite:///./data/bot.db
    if ":///" in url:
        raw_path = url.split(":///", 1)[1]
        if raw_path and raw_path != ":memory:" and not raw_path.startswith(":memory:"):
            path = Path(raw_path)
            if path.parent and str(path.parent) not in {"", "."}:
                path.parent.mkdir(parents=True, exist_ok=True)


def init_engine(settings: Settings):
    global _engine, _session_factory
    url = settings.sqlalchemy_url()
    _ensure_sqlite_dir(url)
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    _engine = create_async_engine(url, echo=False, **kwargs)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def create_tables() -> None:
    if _engine is None:
        raise RuntimeError("Engine is not initialized")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Session factory is not initialized")
    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Session factory is not initialized")
    return _session_factory
