from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from services.gamification.domain.model.mini_boss import MiniBoss


class MiniBossRepository(ABC):
    """Porta Secundária (Driven/Output Port) para persistência de Mini-Bosses."""

    @abstractmethod
    async def get_by_id(self, boss_id: UUID, tenant_id: str | None = None) -> MiniBoss | None:
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str, tenant_id: str | None = None) -> MiniBoss | None:
        pass

    @abstractmethod
    async def save(self, boss: MiniBoss) -> MiniBoss:
        pass

    @abstractmethod
    async def list_active_by_guild(self, guild_id: UUID, tenant_id: str | None = None) -> List[MiniBoss]:
        pass

    @abstractmethod
    async def list_all(self, tenant_id: str | None = None) -> List[MiniBoss]:
        pass
