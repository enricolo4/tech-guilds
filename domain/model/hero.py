from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class HeroClass(str, Enum):
    NOVICE = "NOVICE"                  # Recém-chegado à guilda / Nível 1
    WARRIOR_BACKEND = "WARRIOR"        # Ferreiro / Backend (Foco em Força e estabilidade)
    MAGE_FRONTEND = "MAGE"             # Ilusionista / Frontend (Foco em UI, UX e Inteligência)
    PALADIN_DEVOPS = "PALADIN"         # Guardião / DevOps & SRE (Foco em Uptime e Constituição)
    RANGER_QA = "RANGER"               # Caçador de Sombras / QA (Foco em encontrar Bugs e Acertos Críticos)
    TACTICIAN_TL = "TACTICIAN"         # Estrategista / Tech Lead & PM (Buffs para a guilda)


@dataclass
class HeroStats:
    strength: int = 10      # Bônus de dano contra Mini-Bosses e finalização de tarefas
    intelligence: int = 10  # Aumenta ganho de EXP pessoal
    constitution: int = 10  # Reduz dano sofrido por incidentes de produção
    perception: int = 10    # Aumenta chances de encontrar recompensas e ouro

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
    """Representa um desenvolvedor/membro de tecnologia dentro da sua Guilda."""
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
    inventory: List[Any] = field(default_factory=list)
    equipped_gear: Dict[str, Any] = field(default_factory=dict)
    active_buffs: Dict[str, float] = field(default_factory=dict)
    skill_cooldowns: Dict[str, int] = field(default_factory=dict)
    unlocked_skins: List[str] = field(default_factory=list)

    @property
    def experience_to_next_level(self) -> int:
        """Cálculo quadrático suave de progressão de nível estilo RPG."""
        return int(100 * (self.level ** 1.5))

    def gain_experience(self, amount: int) -> bool:
        """Adiciona EXP e retorna True se o personagem subiu de nível."""
        leveled_up = False
        # Aplica bônus de inteligência (ex: cada ponto acima de 10 dá +2% de EXP)
        int_bonus = max(0, (self.stats.intelligence - 10) * 0.02)
        buff_multiplier = self.active_buffs.get("exp_multiplier", 1.0)
        total_xp = int(amount * (1.0 + int_bonus) * buff_multiplier)
        self.experience += total_xp

        while self.experience >= self.experience_to_next_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            self._increase_stats_on_level_up()
            self.health = self.max_health  # Cura total ao subir de nível
            self.mana = self.max_mana
            leveled_up = True

        return leveled_up

    def gain_gold(self, amount: int) -> None:
        per_bonus = max(0, (self.stats.perception - 10) * 0.02)
        self.gold += int(amount * (1.0 + per_bonus))

    def spend_gold(self, amount: int) -> bool:
        """Gasta ouro do herói. Retorna True se o herói possuía saldo suficiente."""
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def take_damage(self, damage: int) -> bool:
        """Aplica dano ao herói. Retorna True se o herói desmaiou (HP <= 0)."""
        con_reduction = max(0, (self.stats.constitution - 10) * 0.5)
        effective_damage = max(1, int(damage - con_reduction))
        self.health = max(0, self.health - effective_damage)
        return self.health == 0

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def use_mana(self, amount: int) -> bool:
        """Consome mana do herói. Retorna True se o herói possuía mana suficiente."""
        if self.mana < amount:
            return False
        self.mana -= amount
        return True

    def restore_mana(self, amount: int) -> None:
        """Restaura mana até o valor máximo."""
        self.mana = min(self.max_mana, self.mana + amount)

    def equip(self, item: Any) -> Optional[Any]:
        """Equipa um item de equipamento e atualiza os atributos (STR, INT, CON, PER).
        Retorna o equipamento anteriormente equipado no slot, se houver."""
        req_lvl = getattr(item, "required_level", 1)
        if self.level < req_lvl:
            raise ValueError(
                f"Hero level {self.level} is lower than required level {req_lvl}"
            )
        allowed = getattr(item, "allowed_class", None)
        if allowed is not None and allowed != self.hero_class:
            raise ValueError(
                f"Hero class {self.hero_class} cannot equip item allowed only for {allowed}"
            )

        raw_slot = getattr(item, "slot", "WEAPON")
        slot_key = raw_slot.value if hasattr(raw_slot, "value") else str(raw_slot)
        old_item = self.equipped_gear.get(slot_key)
        if old_item is not None and hasattr(old_item, "bonus_stats"):
            self.stats = self.stats - old_item.bonus_stats

        self.equipped_gear[slot_key] = item
        if hasattr(item, "bonus_stats"):
            self.stats = self.stats + item.bonus_stats

        return old_item

    def unequip(self, slot: Any) -> Optional[Any]:
        """Desequipa o item do slot especificado e deduz os bônus dos atributos."""
        slot_key = slot.value if hasattr(slot, "value") else str(slot)
        old_item = self.equipped_gear.pop(slot_key, None)
        if old_item is not None and hasattr(old_item, "bonus_stats"):
            self.stats = self.stats - old_item.bonus_stats
        return old_item

    def is_skill_on_cooldown(self, skill_id: str) -> bool:
        return self.skill_cooldowns.get(skill_id, 0) > 0

    def set_skill_cooldown(self, skill_id: str, turns: int) -> None:
        if turns > 0:
            self.skill_cooldowns[skill_id] = turns

    def tick_cooldowns(self) -> None:
        """Diminui em 1 rodada todos os tempos de recarga ativos."""
        for skill_id in list(self.skill_cooldowns.keys()):
            if self.skill_cooldowns[skill_id] > 0:
                self.skill_cooldowns[skill_id] -= 1
            if self.skill_cooldowns[skill_id] <= 0:
                del self.skill_cooldowns[skill_id]

    def assign_class(self, new_class: HeroClass) -> None:
        """Altera a classe do herói e redistribui bônus iniciais."""
        self.hero_class = new_class
        if new_class == HeroClass.WARRIOR_BACKEND:
            self.stats.strength += 5
        elif new_class == HeroClass.MAGE_FRONTEND:
            self.stats.intelligence += 5
        elif new_class == HeroClass.PALADIN_DEVOPS:
            self.stats.constitution += 5
        elif new_class == HeroClass.RANGER_QA:
            self.stats.perception += 5
        elif new_class == HeroClass.TACTICIAN_TL:
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
