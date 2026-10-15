from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Adventure:
    """Representa um Épico ou Milestone (conjunto de Quests que a Guilda enfrenta junto)."""
    id: UUID = field(default_factory=uuid4)
    external_id: str = ""           # ex: "EPIC-90"
    title: str = ""
    guild_id: UUID = field(default_factory=uuid4)
    total_quests: int = 0
    completed_quests: int = 0
    is_completed: bool = False
    reward_guild_xp: int = 500      # Grande recompensa coletiva ao fechar o épico
    reward_guild_gold: int = 200

    @property
    def progress_percentage(self) -> float:
        if self.total_quests == 0:
            return 0.0
        return min(100.0, (self.completed_quests / self.total_quests) * 100.0)

    def register_quest_completion(self) -> bool:
        """Incrementa o progresso. Se todas as quests foram finalizadas, completa a aventura."""
        self.completed_quests += 1
        if self.completed_quests >= self.total_quests and not self.is_completed:
            self.is_completed = True
            return True
        return False
