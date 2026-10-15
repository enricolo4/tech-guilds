import os
from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/tech_guilds"
DATABASE_URL = os.getenv("GUILDS_DATABASE_URL", os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

# Metadata associado ao schema 'guilds'
metadata = MetaData(schema="guilds")


class Base(DeclarativeBase):
    """Classe base declarativa do SQLAlchemy para o schema 'guilds'."""
    metadata = metadata


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


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI / Gerador para fornecer sessões assíncronas do banco."""
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
    """Cria tabelas no banco de dados (útil para desenvolvimento e testes integrados)."""
    current_engine = target_engine or engine
    async with current_engine.begin() as conn:
        # Se for PostgreSQL, garante criação do schema guilds
        if current_engine.dialect.name == "postgresql":
            from sqlalchemy import text
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS guilds"))
        await conn.run_sync(Base.metadata.create_all)
