from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from services.guilds.domain.model.guild_member import GuildMember


class GuildMemberRepository(ABC):
    """Porta Secundária (Driven Port) para persistência e consulta da projeção de membros de guilda."""

    @abstractmethod
    async def save(self, member: GuildMember) -> GuildMember:
        """Salva ou atualiza a projeção de um membro."""
        pass

    @abstractmethod
    async def find_by_hero_id(self, hero_id: UUID) -> GuildMember | None:
        """Busca a projeção do membro pelo ID do herói."""
        pass

    @abstractmethod
    async def find_by_guild_id(self, guild_id: UUID) -> List[GuildMember]:
        """Lista todos os membros vinculados a uma determinada guilda."""
        pass

    @abstractmethod
    async def update_guild_assignment(self, hero_id: UUID, guild_id: UUID | None) -> GuildMember | None:
        """Atualiza a associação de guilda de um membro."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0, tenant_id: str | None = None) -> List[GuildMember]:
        """Lista todos os membros com paginação e filtro de tenant."""
        pass

