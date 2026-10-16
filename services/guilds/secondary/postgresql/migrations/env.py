import asyncio
from logging.config import fileConfig
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Configuração de logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Garante importação do projeto
project_root = str(Path(__file__).resolve().parents[5])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.guilds.secondary.postgresql.database import Base, DATABASE_URL
import services.guilds.secondary.postgresql.models  # noqa: F401

target_metadata = Base.metadata
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Executa migrações no modo offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="guilds",
        include_schemas=True,
    )

    with context.begin_transaction():
        context.execute("CREATE SCHEMA IF NOT EXISTS guilds")
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # Garante a existência do schema 'guilds' antes de gravar o versionamento
    if connection.dialect.name == "postgresql":
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS guilds"))

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="guilds",
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Executa migrações assíncronas."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
        await connection.commit()

    await connectable.dispose()


def run_migrations_online() -> None:
    """Executa migrações no modo online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
