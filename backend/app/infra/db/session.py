"""Async engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.infra.db.models import Base


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    ensure_sqlite_parent_dir(database_url)
    return create_async_engine(database_url, echo=echo, future=True)


def ensure_sqlite_parent_dir(database_url: str) -> None:
    """SQLite will not create the directory holding its own file.

    Exported rather than private because Alembic builds its own engine and
    needs the same guarantee; doing it in one place means every entry point --
    the app, the CLI and migrations -- gets it instead of only the ones that
    remember to.

    Uses SQLAlchemy's own URL parser: hand-rolling it gets absolute paths
    wrong, because ``sqlite+aiosqlite:////abs/path`` and
    ``sqlite+aiosqlite:///rel/path`` differ by a single slash.
    """
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return
    if not url.database or url.database == ":memory:":
        return
    Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_all(engine: AsyncEngine) -> None:
    """Create tables directly.

    Used for tests and first-run local development. Alembic owns schema changes
    from that point on -- see backend/alembic/.
    """
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """One transaction, committed on success and rolled back on any exception."""
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
