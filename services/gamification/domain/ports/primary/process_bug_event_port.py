from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from services.gamification.domain.model.mini_boss import MiniBoss, BossSeverity
from services.gamification.domain.model.hero_progression import HeroProgression


@dataclass
class ProcessBugEventCommand:
    external_id: str
    title: str
    guild_id: UUID
    severity: BossSeverity
    is_resolved: bool
    resolver_email: str | None = None
    resolver_hero_id: UUID | None = None
    tenant_id: str = "default"


@dataclass
class ProcessBugEventResult:
    mini_boss: MiniBoss
    is_defeated: bool
    bounty_hero_xp: int = 0
    bounty_guild_xp: int = 0
    bounty_gold: int = 0
    hero_leveled_up: bool = False
    hero_progression: HeroProgression | None = None


class ProcessBugEventPort(ABC):
    """Porta Primária para eventos de bugs e incidentes (Mini-Bosses)."""

    @abstractmethod
    async def execute(self, cmd: ProcessBugEventCommand) -> ProcessBugEventResult:
        pass
