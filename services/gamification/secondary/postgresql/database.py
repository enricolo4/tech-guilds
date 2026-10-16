import os
import uuid
from typing import AsyncGenerator
from sqlalchemy import CHAR, event, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/tech_guilds"
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
    """Classe base declarativa do SQLAlchemy para o microsserviço de gamificação."""
    pass


# Suporte universal a UUID para PostgreSQL e SQLite (testes)
class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(str(value))
            return value


async def get_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """Dependency / Generator para obter sessões de banco de dados assíncronas com fallback seguro."""
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


async def init_models(target_engine=None):
    """Cria schema 'gamification' e todas as tabelas no banco de dados."""
    current_engine = target_engine or engine
    if current_engine.dialect.name == "sqlite":
        @event.listens_for(current_engine.sync_engine, "connect")
        def attach_sqlite_schema(dbapi_conn, connection_record):
            try:
                dbapi_conn.execute("ATTACH DATABASE ':memory:' AS gamification")
            except Exception:
                pass

    async with current_engine.begin() as conn:
        if current_engine.dialect.name == "postgresql":
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS gamification"))
        await conn.run_sync(Base.metadata.create_all)
