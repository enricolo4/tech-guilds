from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from ...model.quest import Quest, QuestStatus, QuestDifficulty, QuestReward


@dataclass
class ProcessCardEventCommand:
    external_id: str
    external_source: str
    title: str
    assignee_email: str
    guild_id: UUID
    new_status: QuestStatus
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False
    adventure_external_id: Optional[str] = None


@dataclass
class ProcessCardEventResult:
    quest: Quest
    reward: Optional[QuestReward] = None
    hero_leveled_up: bool = False
    guild_leveled_up: bool = False
    adventure_completed: bool = False


class ProcessCardEventPort(ABC):
    """Porta Primária (Driving/Input Port) para processamento de eventos de cards (Linear, Jira, GitHub)."""
    @abstractmethod
    async def execute(self, cmd: ProcessCardEventCommand) -> ProcessCardEventResult:
        pass
