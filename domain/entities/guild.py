from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class Guild:
    """Representa um Squad ou time de engenharia organizado como uma Guilda."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    level: int = 1
    experience: int = 0
    treasury_gold: int = 0
    member_ids: List[UUID] = field(default_factory=list)
    active_adventure_id: Optional[UUID] = None
    purchased_perks: List[str] = field(default_factory=list)
    active_buffs: Dict[str, float] = field(default_factory=dict)
    shield_points: int = 0

    @property
    def experience_to_next_level(self) -> int:
        """Cálculo de progressão de nível da Guilda."""
        return int(500 * (self.level ** 1.4))

    def gain_experience(self, amount: int) -> bool:
        """Adiciona EXP coletiva para o Squad. Retorna True se a guilda subiu de nível."""
        leveled_up = False
        multiplier = self.active_buffs.get("squad_exp_multiplier", 1.0)
        self.experience += int(amount * multiplier)
        while self.experience >= self.experience_to_next_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            leveled_up = True
        return leveled_up

    def deposit_gold(self, amount: int) -> None:
        self.treasury_gold += amount

    def spend_gold(self, amount: int) -> bool:
        """Gasta ouro do tesouro da Guilda. Retorna True se o saldo for suficiente."""
        if self.treasury_gold < amount:
            return False
        self.treasury_gold -= amount
        return True

    def add_perk(self, perk: str) -> None:
        """Registra um benefício/perk adquirido pelo Squad."""
        self.purchased_perks.append(perk)

    def apply_shield(self, points: int) -> None:
        """Adiciona pontos de escudo protetor da guilda."""
        self.shield_points += points

    def take_damage(self, damage: int) -> int:
        """Aplica dano ao Squad, mitigado por escudo e redução de dano. Retorna o dano real sofrido."""
        reduction = self.active_buffs.get("damage_reduction", 0.0)
        mitigated_damage = int(damage * (1.0 - reduction))
        if self.shield_points > 0:
            if self.shield_points >= mitigated_damage:
                self.shield_points -= mitigated_damage
                return 0
            else:
                remaining = mitigated_damage - self.shield_points
                self.shield_points = 0
                return remaining
        return mitigated_damage

    def add_member(self, hero_id: UUID) -> None:
        if hero_id not in self.member_ids:
            self.member_ids.append(hero_id)

    def remove_member(self, hero_id: UUID) -> None:
        if hero_id in self.member_ids:
            self.member_ids.remove(hero_id)
