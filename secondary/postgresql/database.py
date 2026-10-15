import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/tech_guilds"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

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


class Base(DeclarativeBase):
    """Classe base declarativa do SQLAlchemy."""
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency / Generator para obter sessões de banco de dados assíncronas."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_models(target_engine=None):
    """Cria todas as tabelas no banco de dados (útil para desenvolvimento e testes)."""
    current_engine = target_engine or engine
    async with current_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
