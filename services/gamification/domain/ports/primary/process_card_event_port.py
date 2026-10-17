from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from services.gamification.domain.model.quest import (
    Quest,
    QuestStatus,
    QuestDifficulty,
    QuestReward,
)
from services.gamification.domain.model.hero_progression import HeroProgression


@dataclass
class ProcessCardEventCommand:
    external_id: str
    external_source: str
    title: str
    guild_id: UUID
    new_status: QuestStatus
    assignee_email: str | None = None
    assignee_hero_id: UUID | None = None
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False
    adventure_id: UUID | None = None
    tenant_id: str = "default"


@dataclass
class ProcessCardEventResult:
    quest: Quest
    reward: QuestReward | None = None
    hero_leveled_up: bool = False
    hero_progression: HeroProgression | None = None


class ProcessCardEventPort(ABC):
    """Porta Primária para processamento de eventos de cards e tarefas (Linear, GitHub)."""

    @abstractmethod
    async def execute(self, cmd: ProcessCardEventCommand) -> ProcessCardEventResult:
        pass
