
from services.guilds.domain.ports.primary.guild_ports import (
    AddMemberPort,
    CreateGuildPort,
    SyncHeroMemberPort,
)
from services.guilds.domain.ports.secondary.guild_member_repository import GuildMemberRepository
from services.guilds.domain.ports.secondary.guild_repository import GuildRepository
from services.guilds.domain.use_cases.add_member import AddMemberUseCase
from services.guilds.domain.use_cases.create_guild import CreateGuildUseCase
from services.guilds.domain.use_cases.sync_hero_member import SyncHeroMemberUseCase
import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.guilds.secondary.postgresql.database import get_db_session
from services.guilds.secondary.postgresql.repositories.postgres_guild_repository import (
    InMemoryGuildMemberRepository,
    InMemoryGuildRepository,
    PostgresGuildMemberRepository,
    PostgresGuildRepository,
)


class DependencyContainer:
    """Container de Injeção de Dependências do microsserviço de Guilds."""

    _instance: "DependencyContainer" | None = None

    def __init__(
        self,
        guild_repository: GuildRepository | None = None,
        member_repository: GuildMemberRepository | None = None,
    ):
        self._guild_repository = guild_repository or InMemoryGuildRepository()
        self._member_repository = member_repository or InMemoryGuildMemberRepository()

        self._create_guild_port: CreateGuildPort = CreateGuildUseCase(
            guild_repository=self._guild_repository,
            member_repository=self._member_repository,
        )
        self._add_member_port: AddMemberPort = AddMemberUseCase(
            guild_repository=self._guild_repository,
            member_repository=self._member_repository,
        )
        self._sync_hero_member_port: SyncHeroMemberPort = SyncHeroMemberUseCase(
            member_repository=self._member_repository,
        )

    @classmethod
    def get_instance(cls) -> "DependencyContainer":
        if cls._instance is None:
            cls._instance = DependencyContainer()
        return cls._instance

    @classmethod
    def reset(cls, container: "DependencyContainer" | None = None) -> None:
        cls._instance = container

    @property
    def guild_repository(self) -> GuildRepository:
        return self._guild_repository

    @property
    def member_repository(self) -> GuildMemberRepository:
        return self._member_repository

    @property
    def create_guild_port(self) -> CreateGuildPort:
        return self._create_guild_port

    @property
    def add_member_port(self) -> AddMemberPort:
        return self._add_member_port

    @property
    def sync_hero_member_port(self) -> SyncHeroMemberPort:
        return self._sync_hero_member_port


def get_container(
    session: AsyncSession | None = Depends(get_db_session),
) -> DependencyContainer:
    if session is not None and os.getenv("TESTING", "false").lower() != "true":
        return DependencyContainer(
            guild_repository=PostgresGuildRepository(session),
            member_repository=PostgresGuildMemberRepository(session),
        )
    return DependencyContainer.get_instance()


def get_create_guild_port(
    container: DependencyContainer = Depends(get_container),
) -> CreateGuildPort:
    return container.create_guild_port


def get_add_member_port(
    container: DependencyContainer = Depends(get_container),
) -> AddMemberPort:
    return container.add_member_port


def get_sync_hero_member_port(
    container: DependencyContainer = Depends(get_container),
) -> SyncHeroMemberPort:
    return container.sync_hero_member_port


def get_guild_repository(
    container: DependencyContainer = Depends(get_container),
) -> GuildRepository:
    return container.guild_repository


def get_guild_member_repository(
    container: DependencyContainer = Depends(get_container),
) -> GuildMemberRepository:
    return container.member_repository
