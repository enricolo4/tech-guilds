from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from services.gamification.domain.model.hero_progression import HeroProgression


@dataclass
class SyncHeroProgressionCommand:
    hero_id: UUID
    name: str
    email: Optional[str] = None
    hero_class: str = "NOVICE"
    level: int = 1
    experience: int = 0
    gold: int = 0
    guild_id: Optional[UUID] = None


@dataclass
class SyncHeroProgressionResult:
    hero_progression: HeroProgression
    created: bool


class SyncHeroProgressionPort(ABC):
    """Porta Primária para sincronização inicial ou atualização da ficha RPG do herói a partir de eventos."""

    @abstractmethod
    async def execute(self, cmd: SyncHeroProgressionCommand) -> SyncHeroProgressionResult:
        pass
