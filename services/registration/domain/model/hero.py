from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class HeroClass(str, Enum):
    NOVICE = "NOVICE"                  # Recém-chegado / Nível 1
    WARRIOR = "WARRIOR"                # Ferreiro / Backend (Força e estabilidade)
    MAGE = "MAGE"                      # Ilusionista / Frontend (Inteligência e UI/UX)
    PALADIN = "PALADIN"                # Guardião / DevOps & SRE (Constituição e Uptime)
    RANGER = "RANGER"                  # Caçador / QA (Percepção e Caça a Bugs)
    TACTICIAN = "TACTICIAN"            # Estrategista / Tech Lead & PM (Buffs)


@dataclass
class HeroStats:
    strength: int = 10      # Bônus de dano e finalização de tarefas
    intelligence: int = 10  # Ganho de EXP pessoal
    constitution: int = 10  # Resistência e redução de danos de incidentes
    perception: int = 10    # Chances de encontrar recompensas e ouro

    @classmethod
    def empty(cls) -> "HeroStats":
        return cls(strength=0, intelligence=0, constitution=0, perception=0)

    def __add__(self, other: "HeroStats") -> "HeroStats":
        return HeroStats(
            strength=self.strength + other.strength,
            intelligence=self.intelligence + other.intelligence,
            constitution=self.constitution + other.constitution,
            perception=self.perception + other.perception,
        )

    def __sub__(self, other: "HeroStats") -> "HeroStats":
        return HeroStats(
            strength=self.strength - other.strength,
            intelligence=self.intelligence - other.intelligence,
            constitution=self.constitution - other.constitution,
            perception=self.perception - other.perception,
        )


@dataclass
class Hero:
    """Modelo puro de Domínio que representa um Herói dentro do ecossistema Tech Guilds."""
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""
    avatar_url: Optional[str] = None
    guild_id: Optional[UUID] = None
    hero_class: HeroClass = HeroClass.NOVICE
    level: int = 1
    experience: int = 0
    gold: int = 0
    health: int = 100
    max_health: int = 100
    mana: int = 100
    max_mana: int = 100
    stats: HeroStats = field(default_factory=HeroStats)

    @property
    def experience_to_next_level(self) -> int:
        return int(100 * (self.level ** 1.5))

    def gain_experience(self, amount: int) -> bool:
        """Adiciona EXP e retorna True se subiu de nível."""
        leveled_up = False
        int_bonus = max(0, (self.stats.intelligence - 10) * 0.02)
        total_xp = int(amount * (1.0 + int_bonus))
        self.experience += total_xp

        while self.experience >= self.experience_to_next_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            self._increase_stats_on_level_up()
            self.health = self.max_health
            self.mana = self.max_mana
            leveled_up = True

        return leveled_up

    def gain_gold(self, amount: int) -> None:
        per_bonus = max(0, (self.stats.perception - 10) * 0.02)
        self.gold += int(amount * (1.0 + per_bonus))

    def assign_class(self, new_class: HeroClass) -> None:
        """Define a classe e redistribui bônus iniciais."""
        self.hero_class = new_class
        if new_class == HeroClass.WARRIOR:
            self.stats.strength += 5
        elif new_class == HeroClass.MAGE:
            self.stats.intelligence += 5
        elif new_class == HeroClass.PALADIN:
            self.stats.constitution += 5
        elif new_class == HeroClass.RANGER:
            self.stats.perception += 5
        elif new_class == HeroClass.TACTICIAN:
            self.stats.intelligence += 2
            self.stats.perception += 2

    def join_guild(self, guild_id: UUID) -> None:
        self.guild_id = guild_id

    def _increase_stats_on_level_up(self) -> None:
        self.max_health += 10
        self.max_mana += 10
        self.mana = self.max_mana
        self.stats.strength += 1
        self.stats.intelligence += 1
        self.stats.constitution += 1
        self.stats.perception += 1
