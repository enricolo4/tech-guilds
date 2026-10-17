from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from services.gamification.domain.model.hero_progression import HeroProgression


class HeroProgressionRepository(ABC):
    """Porta Secundária (Driven/Output Port) para persistência da ficha RPG do herói."""

    @abstractmethod
    async def get_by_id(self, hero_id: UUID, tenant_id: str | None = None) -> HeroProgression | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: str | None = None) -> HeroProgression | None:
        pass

    @abstractmethod
    async def save(self, hero: HeroProgression) -> HeroProgression:
        pass

    @abstractmethod
    async def list_by_guild(self, guild_id: UUID, tenant_id: str | None = None) -> List[HeroProgression]:
        pass

    @abstractmethod
    async def list_all(self, tenant_id: str | None = None) -> List[HeroProgression]:
        pass
