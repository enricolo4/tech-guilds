import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/tech_guilds"
DATABASE_URL = os.getenv("REGISTRATION_DATABASE_URL", os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Dependency do FastAPI / Gerador para fornecer sessões assíncronas do schema 'registration'."""
    if os.getenv("TESTING", "false").lower() == "true":
        yield None
        return

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
