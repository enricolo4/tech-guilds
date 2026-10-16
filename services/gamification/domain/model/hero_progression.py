from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID, uuid4

from .item import Equipment, EquipmentSlot


@dataclass
class HeroProgressionStats:
    strength: int = 10
    intelligence: int = 10
    constitution: int = 10
    perception: int = 10

    def to_dict(self) -> Dict[str, int]:
        return {
            "strength": self.strength,
            "intelligence": self.intelligence,
            "constitution": self.constitution,
            "perception": self.perception,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "HeroProgressionStats":
        if not data:
            return cls()
        return cls(
            strength=int(data.get("strength", 10)),
            intelligence=int(data.get("intelligence", 10)),
            constitution=int(data.get("constitution", 10)),
            perception=int(data.get("perception", 10)),
        )


@dataclass
class HeroProgression:
    """Ficha RPG de progressão do Herói (Nível, EXP, Ouro, Vida, Mana e Atributos)."""
    hero_id: UUID
    name: str
    email: str | None = None
    hero_class: str = "NOVICE"
    level: int = 1
    exp: int = 0
    gold: int = 0
    hp: int = 100
    max_hp: int = 100
    mana: int = 100
    max_mana: int = 100
    stats: HeroProgressionStats = field(default_factory=HeroProgressionStats)
    guild_id: UUID | None = None
    equipped_gear: Dict[str, Any] = field(default_factory=dict)
    active_buffs: Dict[str, float] = field(default_factory=dict)
    skill_cooldowns: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.hero_id, str):
            self.hero_id = UUID(self.hero_id)
        if isinstance(self.guild_id, str):
            self.guild_id = UUID(self.guild_id)
        if isinstance(self.stats, dict):
            self.stats = HeroProgressionStats.from_dict(self.stats)

    @property
    def experience_to_next_level(self) -> int:
        """Cálculo quadrático suave de progressão de nível estilo RPG."""
        return int(100 * (self.level ** 1.5))

    def gain_experience(self, amount: int) -> bool:
        """Adiciona EXP e retorna True se o personagem subiu de nível."""
        leveled_up = False
        int_bonus = max(0, (self.stats.intelligence - 10) * 0.02)
        buff_multiplier = self.active_buffs.get("exp_multiplier", 1.0)
        total_xp = int(amount * (1.0 + int_bonus) * buff_multiplier)
        self.exp += total_xp

        while self.exp >= self.experience_to_next_level:
            self.exp -= self.experience_to_next_level
            self.level += 1
            self._increase_stats_on_level_up()
            self.hp = self.max_hp
            self.mana = self.max_mana
            leveled_up = True

        return leveled_up

    def gain_gold(self, amount: int) -> None:
        per_bonus = max(0, (self.stats.perception - 10) * 0.02)
        self.gold += int(amount * (1.0 + per_bonus))

    def spend_gold(self, amount: int) -> bool:
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def take_damage(self, damage: int) -> bool:
        """Aplica dano ao herói. Retorna True se o herói desmaiou (HP <= 0)."""
        con_reduction = max(0, (self.stats.constitution - 10) * 0.5)
        effective_damage = max(1, int(damage - con_reduction))
        self.hp = max(0, self.hp - effective_damage)
        return self.hp == 0

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + amount)

    def use_mana(self, amount: int) -> bool:
        if self.mana < amount:
            return False
        self.mana -= amount
        return True

    def restore_mana(self, amount: int) -> None:
        self.mana = min(self.max_mana, self.mana + amount)

    def equip(self, item: Equipment) -> Any | None:
        if self.level < item.required_level:
            raise ValueError(
                f"Hero level {self.level} is lower than required level {item.required_level}"
            )
        if item.allowed_class is not None and item.allowed_class != self.hero_class:
            raise ValueError(
                f"Hero class {self.hero_class} cannot equip item allowed only for {item.allowed_class}"
            )

        slot_key = item.slot.value if hasattr(item.slot, "value") else str(item.slot)
        old_item_data = self.equipped_gear.get(slot_key)

        # Se já existia item no slot, remove atributos antigos
        if old_item_data and isinstance(old_item_data, dict):
            self.stats.strength -= old_item_data.get("bonus_strength", 0)
            self.stats.intelligence -= old_item_data.get("bonus_intelligence", 0)
            self.stats.constitution -= old_item_data.get("bonus_constitution", 0)
            self.stats.perception -= old_item_data.get("bonus_perception", 0)

        # Aplica novo item
        self.equipped_gear[slot_key] = {
            "id": str(item.id),
            "name": item.name,
            "slot": slot_key,
            "bonus_strength": item.bonus_strength,
            "bonus_intelligence": item.bonus_intelligence,
            "bonus_constitution": item.bonus_constitution,
            "bonus_perception": item.bonus_perception,
        }
        self.stats.strength += item.bonus_strength
        self.stats.intelligence += item.bonus_intelligence
        self.stats.constitution += item.bonus_constitution
        self.stats.perception += item.bonus_perception

        return old_item_data

    def unequip(self, slot: Any) -> Any | None:
        slot_key = slot.value if hasattr(slot, "value") else str(slot)
        old_item_data = self.equipped_gear.pop(slot_key, None)
        if old_item_data and isinstance(old_item_data, dict):
            self.stats.strength -= old_item_data.get("bonus_strength", 0)
            self.stats.intelligence -= old_item_data.get("bonus_intelligence", 0)
            self.stats.constitution -= old_item_data.get("bonus_constitution", 0)
            self.stats.perception -= old_item_data.get("bonus_perception", 0)
        return old_item_data

    def is_skill_on_cooldown(self, skill_id: str) -> bool:
        return self.skill_cooldowns.get(skill_id, 0) > 0

    def set_skill_cooldown(self, skill_id: str, turns: int) -> None:
        if turns > 0:
            self.skill_cooldowns[skill_id] = turns

    def tick_cooldowns(self) -> None:
        for skill_id in list(self.skill_cooldowns.keys()):
            if self.skill_cooldowns[skill_id] > 0:
                self.skill_cooldowns[skill_id] -= 1
            if self.skill_cooldowns[skill_id] <= 0:
                del self.skill_cooldowns[skill_id]

    def _increase_stats_on_level_up(self) -> None:
        self.max_hp += 10
        self.max_mana += 10
        self.stats.strength += 1
        self.stats.intelligence += 1
        self.stats.constitution += 1
        self.stats.perception += 1
