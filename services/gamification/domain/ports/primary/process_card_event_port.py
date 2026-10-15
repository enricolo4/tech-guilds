from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
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
    assignee_email: Optional[str] = None
    assignee_hero_id: Optional[UUID] = None
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False
    adventure_id: Optional[UUID] = None


@dataclass
class ProcessCardEventResult:
    quest: Quest
    reward: Optional[QuestReward] = None
    hero_leveled_up: bool = False
    hero_progression: Optional[HeroProgression] = None


class ProcessCardEventPort(ABC):
    """Porta Primária para processamento de eventos de cards e tarefas (Linear, GitHub)."""

    @abstractmethod
    async def execute(self, cmd: ProcessCardEventCommand) -> ProcessCardEventResult:
        pass
