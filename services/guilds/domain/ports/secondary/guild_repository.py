from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from services.guilds.domain.model.guild import Guild


class GuildRepository(ABC):
    """Porta Secundária (Driven Port) para persistência e consulta de Guildas."""

    @abstractmethod
    async def save(self, guild: Guild) -> Guild:
        """Salva ou atualiza uma guilda."""
        pass

    @abstractmethod
    async def find_by_id(self, guild_id: UUID, tenant_id: str | None = None) -> Guild | None:
        """Busca uma guilda pelo identificador único."""
        pass

    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: str | None = None) -> Guild | None:
        """Busca uma guilda pelo nome exato (opcionalmente filtrado por tenant_id)."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0, tenant_id: str | None = None) -> List[Guild]:
        """Lista todas as guildas com paginação e isolamento por tenant."""
        pass

    @abstractmethod
    async def delete(self, guild_id: UUID) -> bool:
        """Remove uma guilda."""
        pass

