from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from services.gamification.domain.model.quest import Quest


class QuestRepository(ABC):
    """Porta Secundária (Driven/Output Port) para persistência de Quests."""

    @abstractmethod
    async def get_by_id(self, quest_id: UUID) -> Optional[Quest]:
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Optional[Quest]:
        pass

    @abstractmethod
    async def save(self, quest: Quest) -> Quest:
        pass

    @abstractmethod
    async def list_by_guild(self, guild_id: UUID) -> List[Quest]:
        pass

    @abstractmethod
    async def list_all(self) -> List[Quest]:
        pass
