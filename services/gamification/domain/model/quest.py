from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class QuestType(str, Enum):
    FEATURE = "FEATURE"
    IMPROVEMENT = "IMPROVEMENT"
    CHORE = "CHORE"


class QuestStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class QuestDifficulty(str, Enum):
    TRIVIAL = "TRIVIAL"   # ~1 Story Point
    EASY = "EASY"         # ~2 Story Points
    MEDIUM = "MEDIUM"     # ~3-5 Story Points
    HARD = "HARD"         # ~8 Story Points


@dataclass
class QuestReward:
    hero_xp: int
    hero_gold: int
    guild_xp: int
    guild_gold: int


@dataclass
class Quest:
    """Representa um card de tarefa originado do Linear, Jira ou GitHub Issues."""
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = "default"
    external_id: str = ""           # ex: "LIN-1024" ou "JIRA-402"
    external_source: str = "linear"  # "linear", "jira", "github"
    title: str = ""
    guild_id: UUID = field(default_factory=uuid4)
    assignee_hero_id: UUID | None = None
    adventure_id: UUID | None = None
    quest_type: QuestType = QuestType.FEATURE
    status: QuestStatus = QuestStatus.TODO
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False

    def calculate_rewards(self) -> QuestReward:
        """Calcula a recompensa em EXP e Ouro com base na dificuldade e bônus de co-op."""
        multiplier_map = {
            QuestDifficulty.TRIVIAL: 1.0,
            QuestDifficulty.EASY: 1.5,
            QuestDifficulty.MEDIUM: 2.5,
            QuestDifficulty.HARD: 4.0,
        }
        mult = multiplier_map.get(self.difficulty, 2.0)
        base_xp = int(30 * mult)
        base_gold = int(10 * mult)

        # Buff cooperativo: Pair Programming dá bônus extra
        coop_bonus = 1.3 if self.is_pair_programming else 1.0

        hero_xp = int(base_xp * coop_bonus)
        hero_gold = int(base_gold * coop_bonus)
        guild_xp = int(base_xp * 0.5)
        guild_gold = int(base_gold * 0.5)

        return QuestReward(
            hero_xp=hero_xp,
            hero_gold=hero_gold,
            guild_xp=guild_xp,
            guild_gold=guild_gold,
        )
