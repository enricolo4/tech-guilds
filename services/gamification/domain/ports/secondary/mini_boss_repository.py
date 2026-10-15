from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from services.gamification.domain.model.mini_boss import MiniBoss


class MiniBossRepository(ABC):
    """Porta Secundária (Driven/Output Port) para persistência de Mini-Bosses."""

    @abstractmethod
    async def get_by_id(self, boss_id: UUID) -> Optional[MiniBoss]:
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Optional[MiniBoss]:
        pass

    @abstractmethod
    async def save(self, boss: MiniBoss) -> MiniBoss:
        pass

    @abstractmethod
    async def list_active_by_guild(self, guild_id: UUID) -> List[MiniBoss]:
        pass

    @abstractmethod
    async def list_all(self) -> List[MiniBoss]:
        pass
