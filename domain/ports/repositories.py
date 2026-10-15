from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.hero import Hero
from ..entities.guild import Guild
from ..entities.quest import Quest
from ..entities.adventure import Adventure
from ..entities.mini_boss import MiniBoss


class HeroRepository(ABC):
    @abstractmethod
    async def get_by_id(self, hero_id: UUID) -> Optional[Hero]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Hero]:
        pass

    @abstractmethod
    async def save(self, hero: Hero) -> Hero:
        pass

    @abstractmethod
    async def list_by_guild(self, guild_id: UUID) -> List[Hero]:
        pass


class GuildRepository(ABC):
    @abstractmethod
    async def get_by_id(self, guild_id: UUID) -> Optional[Guild]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Guild]:
        pass

    @abstractmethod
    async def save(self, guild: Guild) -> Guild:
        pass

    @abstractmethod
    async def list_all(self) -> List[Guild]:
        pass


class QuestRepository(ABC):
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
    async def list_by_adventure(self, adventure_id: UUID) -> List[Quest]:
        pass

    @abstractmethod
    async def list_by_guild(self, guild_id: UUID) -> List[Quest]:
        pass


class AdventureRepository(ABC):
    @abstractmethod
    async def get_by_id(self, adventure_id: UUID) -> Optional[Adventure]:
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Optional[Adventure]:
        pass

    @abstractmethod
    async def save(self, adventure: Adventure) -> Adventure:
        pass

    @abstractmethod
    async def get_active_by_guild(self, guild_id: UUID) -> Optional[Adventure]:
        pass


class MiniBossRepository(ABC):
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
