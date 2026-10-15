from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union
from uuid import UUID

from services.gamification.domain.model.hero_progression import HeroProgression
from services.gamification.domain.model.skill import Skill


@dataclass
class CastSkillCommand:
    hero_id: UUID
    skill_id: str
    target_boss_id: Optional[UUID] = None
    target_guild_id: Optional[UUID] = None


@dataclass
class CastSkillResult:
    hero: HeroProgression
    skill: Skill
    success: bool
    message: str
    damage_dealt: int = 0
    boss_defeated: bool = False
    exp_multiplier: float = 1.0
    squad_damage_reduction: float = 0.0
    squad_exp_buff: int = 0


class CastSkillPort(ABC):
    """Porta Primária para conjuração de habilidades ativas de classe."""

    @abstractmethod
    async def execute(
        self,
        cmd_or_hero_id: Union[CastSkillCommand, UUID],
        skill_id: Optional[str] = None,
        target_boss_id: Optional[UUID] = None,
        target_guild_id: Optional[UUID] = None,
    ) -> CastSkillResult:
        pass
