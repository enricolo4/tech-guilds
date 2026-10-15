from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from services.guilds.domain.model.guild import Guild


class GuildRepository(ABC):
    """Porta Secundária (Driven Port) para persistência e consulta de Guildas."""

    @abstractmethod
    async def save(self, guild: Guild) -> Guild:
        """Salva ou atualiza uma guilda."""
        pass

    @abstractmethod
    async def find_by_id(self, guild_id: UUID) -> Optional[Guild]:
        """Busca uma guilda pelo identificador único."""
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Guild]:
        """Busca uma guilda pelo nome exato."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Guild]:
        """Lista todas as guildas com paginação."""
        pass

    @abstractmethod
    async def delete(self, guild_id: UUID) -> bool:
        """Remove uma guilda."""
        pass
