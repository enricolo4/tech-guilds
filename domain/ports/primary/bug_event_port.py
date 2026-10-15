from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from ...model.mini_boss import MiniBoss, BossSeverity


@dataclass
class BugEventCommand:
    external_id: str
    title: str
    guild_id: UUID
    severity: BossSeverity
    is_resolved: bool
    resolver_email: Optional[str] = None


@dataclass
class BugEventResult:
    mini_boss: MiniBoss
    is_defeated: bool
    bounty_hero_xp: int = 0
    bounty_guild_xp: int = 0


class ProcessBugEventPort(ABC):
    """Porta Primária (Driving/Input Port) para eventos de bugs e incidentes (Mini-Bosses)."""
    @abstractmethod
    async def execute(self, cmd: BugEventCommand) -> BugEventResult:
        pass
