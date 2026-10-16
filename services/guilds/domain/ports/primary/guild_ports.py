from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from services.guilds.domain.model.guild import Guild
from services.guilds.domain.model.guild_member import GuildMember


@dataclass
class CreateGuildCommand:
    """Comando para criar uma nova Guilda."""
    name: str
    description: str = ""
    creator_hero_id: UUID | None = None


@dataclass
class CreateGuildResult:
    """Resultado da criação de uma Guilda."""
    guild: Guild
    success: bool = True
    message: str = "Guild created successfully"


class CreateGuildPort(ABC):
    """Porta Primária (Driving Port) para criação de Guildas."""

    @abstractmethod
    async def execute(self, cmd: CreateGuildCommand) -> CreateGuildResult:
        pass


@dataclass
class AddMemberCommand:
    """Comando para adicionar um membro/herói a uma Guilda."""
    guild_id: UUID
    hero_id: UUID


@dataclass
class AddMemberResult:
    """Resultado da adição de um membro."""
    guild_id: UUID
    hero_id: UUID
    success: bool = True
    message: str = "Member added to guild successfully"


class AddMemberPort(ABC):
    """Porta Primária (Driving Port) para adição de membros a uma Guilda."""

    @abstractmethod
    async def execute(self, cmd: AddMemberCommand) -> AddMemberResult:
        pass


@dataclass
class SyncHeroMemberCommand:
    """Comando para sincronizar a projeção do membro a partir do evento de herói registrado."""
    hero_id: UUID
    name: str
    email: str
    hero_class: str
    avatar_url: str | None = None
    level: int = 1
    occurred_at: str | None = None


@dataclass
class SyncHeroMemberResult:
    """Resultado da sincronização da projeção de membro."""
    member: GuildMember
    is_new: bool = True


class SyncHeroMemberPort(ABC):
    """Porta Primária (Driving Port) para sincronização de membro (HeroRegisteredEvent)."""

    @abstractmethod
    async def execute(self, cmd: SyncHeroMemberCommand) -> SyncHeroMemberResult:
        pass
